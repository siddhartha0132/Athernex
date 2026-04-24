"""Telephony Module with Twilio integration"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
import websockets
from websockets.server import WebSocketServerProtocol

from src.event_bus.event_bus import EventBus, EventEnvelope


class TelephonyModule:
    """Manages phone calls and audio streaming"""
    
    def __init__(
        self,
        event_bus: EventBus,
        account_sid: str,
        auth_token: str,
        webhook_url: str
    ):
        self.event_bus = event_bus
        self.twilio_client = Client(account_sid, auth_token)
        self.webhook_url = webhook_url
        self.active_calls: Dict[str, Dict] = {}
        
        # Subscribe to audio_output events
        self.event_bus.subscribe("audio_output", self._handle_audio_output)
    
    def initiate_call(
        self,
        phone_number: str,
        order_id: str,
        attempt_number: int = 1
    ) -> str:
        """Initiate outgoing call"""
        session_id = str(uuid.uuid4())
        
        # Publish call_initiated event
        self.event_bus.publish(EventEnvelope(
            event_type="call_initiated",
            source_module="telephony_module",
            session_id=session_id,
            data={
                "phone_number": phone_number,
                "order_id": order_id,
                "attempt_number": attempt_number,
                "scheduled_time": datetime.utcnow().isoformat()
            }
        ))
        
        # Create TwiML response with WebSocket stream
        twiml = VoiceResponse()
        connect = Connect()
        connect.stream(url=f"{self.webhook_url}/stream/{session_id}")
        twiml.append(connect)
        
        # Initiate call via Twilio
        call = self.twilio_client.calls.create(
            to=phone_number,
            from_="+1234567890",  # Your Twilio number
            twiml=str(twiml),
            status_callback=f"{self.webhook_url}/status/{session_id}",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed']
        )
        
        # Store call info
        self.active_calls[session_id] = {
            "call_sid": call.sid,
            "phone_number": phone_number,
            "order_id": order_id,
            "websocket": None,
            "start_time": datetime.utcnow()
        }
        
        return session_id
    
    async def handle_websocket(
        self,
        websocket: WebSocketServerProtocol,
        session_id: str
    ):
        """Handle WebSocket connection for audio streaming"""
        # Store WebSocket connection
        if session_id in self.active_calls:
            self.active_calls[session_id]["websocket"] = websocket
            
            # Publish call_connected event
            self.event_bus.publish(EventEnvelope(
                event_type="call_connected",
                source_module="telephony_module",
                session_id=session_id,
                data={
                    "phone_number": self.active_calls[session_id]["phone_number"],
                    "order_id": self.active_calls[session_id]["order_id"],
                    "connection_time": datetime.utcnow().isoformat(),
                    "provider": "twilio"
                }
            ))
        
        try:
            # Receive audio from call
            async for message in websocket:
                if isinstance(message, bytes):
                    # Publish audio_input event
                    self.event_bus.publish(EventEnvelope(
                        event_type="audio_input",
                        source_module="telephony_module",
                        session_id=session_id,
                        data={
                            "chunk_sequence": 0,  # Track sequence
                            "audio_data": message.hex(),
                            "format": "mulaw",
                            "sample_rate": 8000,
                            "duration_ms": 20
                        }
                    ))
        except websockets.exceptions.ConnectionClosed:
            self.end_call(session_id, "dropped")
    
    def end_call(self, session_id: str, reason: str = "completed"):
        """End call and cleanup"""
        if session_id not in self.active_calls:
            return
        
        call_info = self.active_calls[session_id]
        
        # Publish call_ended event
        duration = (datetime.utcnow() - call_info["start_time"]).total_seconds()
        self.event_bus.publish(EventEnvelope(
            event_type="call_ended",
            source_module="telephony_module",
            session_id=session_id,
            data={
                "phone_number": call_info["phone_number"],
                "order_id": call_info["order_id"],
                "end_reason": reason,
                "duration_seconds": duration,
                "final_state": "unknown"  # Will be updated by state machine
            }
        ))
        
        # Cleanup
        if call_info["websocket"]:
            asyncio.create_task(call_info["websocket"].close())
        del self.active_calls[session_id]
    
    def _handle_audio_output(self, envelope: EventEnvelope):
        """Handle audio_output events and stream to call"""
        session_id = envelope.session_id
        if session_id not in self.active_calls:
            return
        
        call_info = self.active_calls[session_id]
        websocket = call_info.get("websocket")
        
        if websocket:
            # Convert hex audio data back to bytes
            audio_data = bytes.fromhex(envelope.data["audio_data"])
            
            # Send to WebSocket (async)
            asyncio.create_task(websocket.send(audio_data))
