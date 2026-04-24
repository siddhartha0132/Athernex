"""
VyapaarSetu AI - Order Confirmation Voice Flow
Extended voice webhooks for order confirmation process
"""

import json
from datetime import datetime
from flask import request
from twilio.twiml.voice_response import VoiceResponse
from models import db, Customer, Order, CallSession, log_audit
from extended_routes import (
    detect_affirmation, run_risk_engine, generate_consent_hash, 
    get_localized
)
from language_detector import detect_language, get_tts_language_code

# Global state for call sessions (in production, use Redis)
call_sessions = {}

def register_voice_routes(app, socketio, sarvam_tts, validate_twilio_request):
    """Register order confirmation voice routes"""
    
    @app.route('/voice/order-confirm', methods=['POST'])
    @validate_twilio_request
    def voice_order_confirm():
        """
        Entry point for the full order confirmation flow.
        Triggered when customer picks up.
        """
        call_sid = request.form.get('CallSid')
        order_id = request.args.get('order_id')
        
        if not order_id:
            return "Invalid request", 400
        
        order = Order.query.filter_by(order_id=order_id).first()
        if not order:
            return "Order not found", 404
        
        customer = order.customer
        
        # Initialize call session
        call_sessions[call_sid] = {
            'order_id': order_id,
            'phase': 'IDENTITY_CHECK',   # State machine phase
            'retry_count': 0,
            'detected_lang': customer.language_preference or 'hi',
            'transcript_log': []
        }
        
        # Create database call session
        db_session = CallSession(
            call_sid=call_sid,
            order_id=order_id,
            customer_phone=customer.phone_number,
            detected_language=customer.language_preference or 'hi'
        )
        db.session.add(db_session)
        db.session.commit()
        
        log_audit('CALL_STARTED', order_id, call_sid, 'ai_bot', f'Order confirmation call started')
        
        # Determine greeting language
        lang = customer.language_preference or 'hi'
        greeting = build_greeting(customer.name, order, lang)
        
        response = VoiceResponse()
        tts_audio = sarvam_tts(greeting, call_sid, get_tts_language_code(lang))
        if tts_audio:
            response.play(tts_audio)
        else:
            response.say(greeting, language=get_tts_language_code(lang))
        
        response.record(
            action=f'/voice/process-order?call_sid={call_sid}&order_id={order_id}',
            method='POST',
            max_length=15,
            play_beep=True,
            timeout=5
        )
        
        # Emit real-time update
        socketio.emit('call_started', {
            'call_sid': call_sid,
            'order_id': order_id,
            'customer_name': customer.name,
            'phase': 'IDENTITY_CHECK'
        })
        
        return str(response), 200, {'Content-Type': 'text/xml'}
    
    @app.route('/voice/process-order', methods=['POST'])
    @validate_twilio_request
    def process_order_call():
        """
        State machine processor — handles each turn of the order confirmation call.
        Phases: IDENTITY_CHECK → ORDER_CONFIRMATION → RISK_CHECK → DONE
        """
        call_sid = request.args.get('call_sid') or request.form.get('CallSid')
        order_id = request.args.get('order_id')
        recording_url = request.form.get('RecordingUrl')
        
        session = call_sessions.get(call_sid, {})
        order = Order.query.filter_by(order_id=order_id).first()
        customer = order.customer
        phase = session.get('phase', 'IDENTITY_CHECK')
        
        # Import STT function (assuming it's available)
        from app import sarvam_stt
        
        # 1. Download + transcribe audio
        transcript = sarvam_stt(recording_url)
        if not transcript:
            return handle_stt_failure(call_sid, order_id, session, socketio, sarvam_tts)
        
        # 2. Detect language from this turn
        detected_lang = detect_language(transcript)
        session['detected_lang'] = detected_lang
        tts_code = get_tts_language_code(detected_lang)
        
        # 3. Log transcript turn
        session['transcript_log'].append({
            'role': 'user', 
            'text': transcript, 
            'lang': detected_lang,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Update database session
        db_session = CallSession.query.filter_by(call_sid=call_sid).first()
        if db_session:
            db_session.detected_language = detected_lang
            db_session.full_transcript = json.dumps(session['transcript_log'])
            db.session.commit()
        
        response = VoiceResponse()
        
        # ══════════════════════════════════════════════════════════════════════════
        # PHASE: IDENTITY_CHECK
        # ══════════════════════════════════════════════════════════════════════════
        if phase == 'IDENTITY_CHECK':
            identity_confirmed = detect_affirmation(transcript, detected_lang)
            
            if identity_confirmed == 'YES':
                session['phase'] = 'ORDER_CONFIRMATION'
                # Read out full order details
                order_details_msg = build_order_details_message(order, detected_lang)
                play_tts(response, order_details_msg, call_sid, tts_code, sarvam_tts)
                response.record(
                    action=f'/voice/process-order?call_sid={call_sid}&order_id={order_id}',
                    max_length=15, play_beep=True, timeout=5
                )
                
                # Emit phase update
                socketio.emit('call_phase_update', {
                    'call_sid': call_sid,
                    'phase': 'ORDER_CONFIRMATION',
                    'transcript': transcript
                })
                
            elif identity_confirmed == 'NO':
                wrong_person_msg = get_localized(detected_lang, {
                    'hi': "Theek hai, maafi chahta hoon. Galat number dial ho gaya. Dhanyawad!",
                    'en': "I'm sorry, I must have the wrong person. Thank you, goodbye!"
                })
                play_tts(response, wrong_person_msg, call_sid, tts_code, sarvam_tts)
                order.status = 'WRONG_PERSON'
                db.session.commit()
                log_audit('WRONG_PERSON', order_id, call_sid, 'ai_bot', 'Customer denied identity')
                socketio.emit('order_update', order.to_dict())
                response.hangup()
                
            else:
                # Ask again
                retry_msg = get_localized(detected_lang, {
                    'hi': f"Kya aap {customer.name} ji hain? Haan ya na boliye.",
                    'en': f"Are you {customer.name}? Please say yes or no."
                })
                play_tts(response, retry_msg, call_sid, tts_code, sarvam_tts)
                response.record(
                    action=f'/voice/process-order?call_sid={call_sid}&order_id={order_id}',
                    max_length=10, play_beep=True
                )
        
        # ══════════════════════════════════════════════════════════════════════════
        # PHASE: ORDER_CONFIRMATION
        # ══════════════════════════════════════════════════════════════════════════
        elif phase == 'ORDER_CONFIRMATION':
            intent = detect_affirmation(transcript, detected_lang)
            session['intent'] = intent
            
            # Update database session
            if db_session:
                db_session.intent_result = intent
                db.session.commit()
            
            if intent == 'YES':
                # Run cybersecurity check
                risk = run_risk_engine(customer, order)
                session['phase'] = 'RISK_CHECKED'
                
                if risk['decision'] == 'SUSPICIOUS':
                    # Flag and hold
                    order.status = 'FLAGGED'
                    order.risk_level = 'SUSPICIOUS'
                    db.session.commit()
                    log_audit('ORDER_FLAGGED', order_id, call_sid, 'ai_bot', risk['reason'])
                    socketio.emit('order_update', order.to_dict())
                    socketio.emit('risk_alert', {'order_id': order_id, 'risk': risk})
                    
                    suspicious_msg = get_localized(detected_lang, {
                        'hi': "Humein kuch verification ki zaroorat hai. Hamara team aapko contact karega.",
                        'en': "We need to verify a few details. Our team will contact you shortly."
                    })
                    play_tts(response, suspicious_msg, call_sid, tts_code, sarvam_tts)
                    response.hangup()
                    
                else:
                    # Generate blockchain hash
                    blockchain_hash = generate_consent_hash(order_id, customer.phone_number, 'CONFIRMED')
                    order.blockchain_hash = blockchain_hash
                    order.status = 'AWAITING_APPROVAL'
                    order.risk_level = risk['decision']
                    db.session.commit()
                    
                    log_audit('CONSENT_RECORDED', order_id, call_sid, 'ai_bot',
                             f'Hash: {blockchain_hash[:16]}...')
                    socketio.emit('order_update', order.to_dict())
                    socketio.emit('approval_needed', order.to_dict())
                    
                    confirmed_msg = get_localized(detected_lang, {
                        'hi': f"Bahut acha! Aapka order confirm ho gaya hai. Order number {order_id} hai. Aapko confirmation message milega. Dhanyawad!",
                        'en': f"Excellent! Your order {order_id} is confirmed. You'll receive a confirmation message shortly. Thank you!"
                    })
                    play_tts(response, confirmed_msg, call_sid, tts_code, sarvam_tts)
                    response.hangup()
            
            elif intent == 'NO':
                order.status = 'REJECTED_BY_CUSTOMER'
                db.session.commit()
                log_audit('ORDER_REJECTED', order_id, call_sid, 'ai_bot', 'Customer said NO')
                socketio.emit('order_update', order.to_dict())
                
                rejected_msg = get_localized(detected_lang, {
                    'hi': "Theek hai, aapka order cancel kar diya gaya hai. Koi pareshani ho toh humse sampark karein. Dhanyawad!",
                    'en': "Understood, your order has been cancelled. Contact us if you need help. Thank you!"
                })
                play_tts(response, rejected_msg, call_sid, tts_code, sarvam_tts)
                response.hangup()
            
            else:
                # UNKNOWN — retry up to 2 times
                session['retry_count'] = session.get('retry_count', 0) + 1
                if session['retry_count'] >= 2:
                    # Escalate to human
                    order.status = 'ESCALATED'
                    db.session.commit()
                    log_audit('ESCALATED', order_id, call_sid, 'ai_bot', 'Too many unclear responses')
                    socketio.emit('escalation_needed', order.to_dict())
                    
                    escalate_msg = get_localized(detected_lang, {
                        'hi': "Hamein samajh nahi aaya. Hamara agent aapko jald call karega.",
                        'en': "I couldn't understand. Our agent will call you back shortly."
                    })
                    play_tts(response, escalate_msg, call_sid, tts_code, sarvam_tts)
                    response.hangup()
                else:
                    retry_msg = get_localized(detected_lang, {
                        'hi': "Kya aap is order ko confirm karna chahte hain? Sirf haan ya na boliye.",
                        'en': "Do you confirm this order? Please say only yes or no."
                    })
                    play_tts(response, retry_msg, call_sid, tts_code, sarvam_tts)
                    response.record(
                        action=f'/voice/process-order?call_sid={call_sid}&order_id={order_id}',
                        max_length=10, play_beep=True
                    )
        
        return str(response), 200, {'Content-Type': 'text/xml'}

def build_greeting(name: str, order: Order, lang: str) -> str:
    """Build personalized greeting message"""
    items_str = ', '.join(json.loads(order.items)) if order.items else 'your items'
    greetings = {
        'hi': f"Namaste {name} ji! Aapka ₹{order.amount:.0f} ka order hai jisme {items_str} hai. Kya aap {name} ji bol rahe hain?",
        'en': f"Hello {name}! You have an order of ₹{order.amount:.0f} for {items_str}. Am I speaking with {name}?",
        'kn': f"Namaskara {name} avare! Nimma ₹{order.amount:.0f} ra order ide. Neevu {name} avara?",
        'mr': f"Namaskar {name} ji! Tumcha ₹{order.amount:.0f} cha order ahe. Tumhi {name} ji ahat ka?"
    }
    return greetings.get(lang, greetings['hi'])

def build_order_details_message(order: Order, lang: str) -> str:
    """Build detailed order confirmation message"""
    items = json.loads(order.items) if order.items else []
    items_str = ', '.join(items) if items else 'items'
    
    messages = {
        'hi': f"Aapka order hai: {items_str}. Total amount ₹{order.amount:.0f} hai. Delivery address: {order.delivery_address}. Kya aap is order ko confirm karte hain?",
        'en': f"Your order is: {items_str}. Total amount is ₹{order.amount:.0f}. Delivery to: {order.delivery_address}. Do you confirm this order?"
    }
    return messages.get(lang, messages['hi'])

def play_tts(response: VoiceResponse, text: str, call_sid: str, tts_code: str, sarvam_tts_func):
    """Helper to play TTS audio with fallback"""
    audio_url = sarvam_tts_func(text, call_sid, tts_code)
    if audio_url:
        response.play(audio_url)
    else:
        response.say(text, language=tts_code)

def handle_stt_failure(call_sid: str, order_id: str, session: dict, socketio, sarvam_tts_func):
    """Handle STT failure with appropriate response"""
    response = VoiceResponse()
    lang = session.get('detected_lang', 'hi')
    tts_code = get_tts_language_code(lang)
    
    error_msg = get_localized(lang, {
        'hi': "Maaf kijiye, main aapki baat samajh nahi paaya. Kripya dobara boliye.",
        'en': "Sorry, I didn't catch that. Please repeat."
    })
    
    play_tts(response, error_msg, call_sid, tts_code, sarvam_tts_func)
    response.record(
        action=f'/voice/process-order?call_sid={call_sid}&order_id={order_id}',
        method='POST',
        max_length=15,
        play_beep=True
    )
    
    return str(response), 200, {'Content-Type': 'text/xml'}