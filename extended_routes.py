"""
VyapaarSetu AI - Extended Flask Routes
New API routes for dashboard and Android app integration
"""

import os
import json
import uuid
import hashlib
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from models import db, Customer, Order, CallSession, AuditLog, log_audit
from language_detector import detect_language, get_language_name, get_tts_language_code

# Configuration from environment
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
BASE_URL = os.getenv('BASE_URL')

# Twilio client will be passed from main app
twilio_client = None

# API Key authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if api_key != os.getenv('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

# JWT authentication for Android app
def require_jwt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid token'}), 401
        
        try:
            token = token.split(' ')[1]
            payload = jwt.decode(token, os.getenv('JWT_SECRET', 'secret'), algorithms=['HS256'])
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def register_extended_routes(app, socketio, twilio_client_instance):
    """Register all extended routes with the Flask app"""
    global twilio_client
    twilio_client = twilio_client_instance
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # OUTBOUND CALL INITIATION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    @app.route('/api/v1/call/initiate', methods=['POST'])
    @require_api_key
    def initiate_call():
        """
        Called by Dashboard or Android app to start an AI confirmation call.
        Body: { "order_id": "ORD123", "phone_number": "+919876543210" }
        """
        data = request.json
        order_id = data.get('order_id')
        phone_number = data.get('phone_number')
        
        if not order_id or not phone_number:
            return jsonify({'error': 'Missing order_id or phone_number'}), 400
        
        order = Order.query.filter_by(order_id=order_id).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        customer = Customer.query.filter_by(phone_number=phone_number).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Update order status
        order.status = 'CALLING'
        db.session.commit()
        
        # Log audit
        log_audit('CALL_INITIATED', order_id, None, 'dashboard', f'Calling {phone_number}')
        
        try:
            # Place Twilio outbound call
            call = twilio_client.calls.create(
                to=phone_number,
                from_=TWILIO_PHONE_NUMBER,
                url=f"{BASE_URL}/voice/order-confirm?order_id={order_id}",
                status_callback=f"{BASE_URL}/call-status",
                status_callback_method='POST'
            )
            
            order.call_sid = call.sid
            db.session.commit()
            
            # Emit real-time event to dashboard
            socketio.emit('order_update', order.to_dict())
            
            return jsonify({
                "success": True, 
                "call_sid": call.sid, 
                "status": "CALLING"
            })
            
        except Exception as e:
            order.status = 'CALL_FAILED'
            db.session.commit()
            log_audit('CALL_FAILED', order_id, None, 'system', f'Error: {str(e)}')
            return jsonify({'error': f'Call failed: {str(e)}'}), 500
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # DASHBOARD API ROUTES
    # ═══════════════════════════════════════════════════════════════════════════════
    
    @app.route('/api/v1/dashboard/stats', methods=['GET'])
    @require_api_key
    def dashboard_stats():
        """Live stats for the dashboard top cards."""
        return get_stats_data()
    
    def get_stats_data():
        """Helper function to get stats data without authentication"""
        total = Order.query.count()
        confirmed = Order.query.filter_by(status='APPROVED').count()
        pending_approval = Order.query.filter_by(status='AWAITING_APPROVAL').count()
        flagged = Order.query.filter_by(status='FLAGGED').count()
        escalated = Order.query.filter_by(status='ESCALATED').count()
        calling = Order.query.filter_by(status='CALLING').count()
        total_revenue = db.session.query(db.func.sum(Order.amount))\
            .filter(Order.status=='APPROVED').scalar() or 0
        
        return jsonify({
            'total_orders': total,
            'confirmed': confirmed,
            'pending_approval': pending_approval,
            'flagged': flagged,
            'escalated': escalated,
            'calling': calling,
            'total_revenue': total_revenue
        })
    
    @app.route('/api/v1/orders', methods=['GET'])
    @require_api_key
    def list_orders():
        """Paginated order list with filters."""
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = Order.query.order_by(Order.created_at.desc())
        if status:
            query = query.filter_by(status=status)
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'orders': [order.to_dict() for order in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        })
    
    @app.route('/api/v1/orders/<order_id>', methods=['GET'])
    @require_api_key
    def get_order(order_id):
        order = Order.query.filter_by(order_id=order_id).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        return jsonify(order.to_dict(detailed=True))
    
    @app.route('/api/v1/orders/<order_id>/approve', methods=['POST'])
    @require_api_key
    def human_approve_order(order_id):
        """Human agent approves or rejects a pending order."""
        data = request.json
        action = data.get('action')  # 'APPROVE' or 'REJECT'
        agent_name = data.get('agent_name', 'Unknown Agent')
        
        order = Order.query.filter_by(order_id=order_id).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if action == 'APPROVE':
            order.status = 'APPROVED'
            order.human_approved_by = agent_name
            order.human_approved_at = datetime.utcnow()
            log_audit('HUMAN_APPROVED', order_id, order.call_sid, f'human:{agent_name}', 'Order approved')
        elif action == 'REJECT':
            order.status = 'REJECTED_BY_AGENT'
            order.human_approved_by = agent_name
            log_audit('HUMAN_REJECTED', order_id, order.call_sid, f'human:{agent_name}', 'Order rejected')
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        db.session.commit()
        socketio.emit('order_update', order.to_dict())
        
        return jsonify({'success': True, 'status': order.status})
    
    @app.route('/api/v1/orders', methods=['POST'])
    @require_api_key
    def create_order():
        """Create a new order from dashboard or Android app."""
        data = request.json
        
        # Validate required fields
        required_fields = ['phone_number', 'customer_name', 'amount']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get or create customer
        customer = Customer.query.filter_by(phone_number=data['phone_number']).first()
        if not customer:
            customer = Customer(
                phone_number=data['phone_number'],
                name=data['customer_name'],
                language_preference=data.get('language', 'hi')
            )
            db.session.add(customer)
            db.session.flush()
        
        # Create order
        order = Order(
            order_id=f"ORD{uuid.uuid4().hex[:8].upper()}",
            customer_id=customer.id,
            items=json.dumps(data.get('items', [])),
            amount=float(data['amount']),
            delivery_address=data.get('delivery_address', ''),
            status='PENDING'
        )
        db.session.add(order)
        db.session.commit()
        
        # Update customer stats
        customer.total_orders += 1
        db.session.commit()
        
        log_audit('ORDER_CREATED', order.order_id, None, 'dashboard', 'New order created')
        socketio.emit('new_order', order.to_dict())
        
        return jsonify({'success': True, 'order_id': order.order_id}), 201
    
    @app.route('/api/v1/audit/<order_id>', methods=['GET'])
    @require_api_key
    def get_audit_log(order_id):
        logs = AuditLog.query.filter_by(order_id=order_id)\
            .order_by(AuditLog.timestamp.asc()).all()
        return jsonify([log.to_dict() for log in logs])
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ANDROID APP AUTHENTICATION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    @app.route('/api/v1/auth/login', methods=['POST'])
    def android_login():
        """Simple login for Android agents."""
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        # Validate against env-configured credentials
        if (username == os.getenv('AGENT_USERNAME') and 
            password == os.getenv('AGENT_PASSWORD')):
            
            token = jwt.encode({
                'user': username,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, os.getenv('JWT_SECRET', 'secret'), algorithm='HS256')
            
            return jsonify({'token': token, 'user': username})
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ANDROID APP PROTECTED ROUTES
    # ═══════════════════════════════════════════════════════════════════════════════
    
    @app.route('/api/v1/mobile/orders', methods=['GET'])
    @require_jwt
    def mobile_orders():
        """Mobile-optimized order list"""
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        query = Order.query.order_by(Order.created_at.desc()).limit(limit)
        if status:
            query = query.filter_by(status=status)
        
        orders = query.all()
        return jsonify([order.to_dict() for order in orders])
    
    @app.route('/api/v1/mobile/orders/<order_id>/call', methods=['POST'])
    @require_jwt
    def mobile_initiate_call(order_id):
        """Mobile call initiation"""
        order = Order.query.filter_by(order_id=order_id).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Use the same logic as dashboard call initiation
        return initiate_call()
    
    @app.route('/api/v1/mobile/stats', methods=['GET'])
    @require_jwt
    def mobile_stats():
        """Mobile dashboard stats"""
        return get_stats_data()

def get_localized(lang: str, messages: dict) -> str:
    """Get localized message based on language"""
    return messages.get(lang, messages.get('hi', messages.get('en', 'Message not available')))

def generate_consent_hash(order_id: str, customer_phone: str, response: str) -> str:
    """
    Generate SHA256 proof of consent.
    SHA256(order_id + customer_phone_hash + response + timestamp)
    """
    timestamp = datetime.utcnow().isoformat()
    phone_hash = hashlib.sha256(customer_phone.encode()).hexdigest()[:16]
    raw = f"{order_id}:{phone_hash}:{response}:{timestamp}"
    return hashlib.sha256(raw.encode()).hexdigest()

def run_risk_engine(customer: Customer, order: Order) -> dict:
    """
    Multi-factor risk assessment.
    Returns: { decision: SAFE/MEDIUM/SUSPICIOUS, reason: str, score: int }
    """
    risk_score = 0
    flags = []
    
    # 1. Repeated cancellation check
    if customer.cancellation_count >= 3:
        risk_score += 40
        flags.append('HIGH_CANCELLATION_RATE')
    
    # 2. Order amount anomaly
    avg_order = db.session.query(db.func.avg(Order.amount))\
        .filter_by(customer_id=customer.id).scalar() or 0
    if avg_order > 0 and order.amount > avg_order * 3:
        risk_score += 25
        flags.append('UNUSUAL_ORDER_AMOUNT')
    
    # 3. Address mismatch (new address for large order)
    past_addresses = [o.delivery_address for o in customer.orders[-5:]]
    if order.delivery_address not in past_addresses and order.amount > 5000:
        risk_score += 20
        flags.append('NEW_ADDRESS_HIGH_VALUE')
    
    # 4. Rapid order frequency
    recent_orders = Order.query.filter_by(customer_id=customer.id)\
        .filter(Order.created_at >= datetime.utcnow() - timedelta(hours=24)).count()
    if recent_orders >= 5:
        risk_score += 30
        flags.append('RAPID_ORDER_FREQUENCY')
    
    # 5. Previously flagged customer
    if Order.query.filter_by(customer_id=customer.id, status='FLAGGED').count() > 0:
        risk_score += 35
        flags.append('PREVIOUSLY_FLAGGED')
    
    decision = 'SAFE' if risk_score < 30 else 'MEDIUM' if risk_score < 60 else 'SUSPICIOUS'
    return {
        'decision': decision,
        'score': risk_score,
        'flags': flags,
        'reason': ', '.join(flags) if flags else 'All checks passed'
    }

def detect_affirmation(text: str, lang: str) -> str:
    """Returns YES / NO / UNKNOWN"""
    text_lower = text.lower().strip()
    
    yes_words = {
        'hi': ['haan', 'ha', 'han', 'ji haan', 'bilkul', 'theek hai', 'confirm', 'yes', 'ok', 'okay', 'sahi'],
        'en': ['yes', 'yeah', 'yep', 'confirm', 'correct', 'right', 'sure', 'ok', 'okay', 'absolutely'],
        'kn': ['houdhu', 'sari', 'confirm', 'yes', 'ok'],
        'mr': ['ho', 'hoy', 'confirm', 'yes', 'baro']
    }
    no_words = {
        'hi': ['nahi', 'na', 'naa', 'cancel', 'mat karo', 'band karo', 'no', 'nope'],
        'en': ['no', 'nope', 'cancel', 'not', "don't", 'negative'],
        'kn': ['ille', 'beda', 'cancel', 'no'],
        'mr': ['nahi', 'nako', 'cancel', 'no']
    }
    
    for word in yes_words.get(lang, yes_words['en']):
        if word in text_lower:
            return 'YES'
    for word in no_words.get(lang, no_words['en']):
        if word in text_lower:
            return 'NO'
    return 'UNKNOWN'