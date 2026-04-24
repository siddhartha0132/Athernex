"""
VyapaarSetu AI - Database Models
SQLAlchemy models for the extended order confirmation system
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import json

db = SQLAlchemy()

class Customer(db.Model):
    """Customer information and history"""
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    language_preference = db.Column(db.String(10), default='hi')
    cancellation_count = db.Column(db.Integer, default=0)
    total_orders = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'name': self.name,
            'language_preference': self.language_preference,
            'cancellation_count': self.cancellation_count,
            'total_orders': self.total_orders,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Order(db.Model):
    """Order information and status tracking"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    customer = db.relationship('Customer', backref='orders')
    items = db.Column(db.Text)  # JSON string
    amount = db.Column(db.Float, nullable=False)
    delivery_address = db.Column(db.Text)
    status = db.Column(db.String(30), default='PENDING')
    # Status flow: PENDING → CALLING → CONFIRMED → REJECTED → FLAGGED → APPROVED → CANCELLED
    risk_level = db.Column(db.String(20))  # SAFE / MEDIUM / SUSPICIOUS
    blockchain_hash = db.Column(db.String(64))
    invoice_path = db.Column(db.String(200))
    human_approved_by = db.Column(db.String(100))
    human_approved_at = db.Column(db.DateTime)
    call_sid = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, detailed=False):
        base = {
            'id': self.id,
            'order_id': self.order_id,
            'customer_name': self.customer.name if self.customer else 'Unknown',
            'customer_phone': self.customer.phone_number if self.customer else 'Unknown',
            'items': json.loads(self.items) if self.items else [],
            'amount': self.amount,
            'delivery_address': self.delivery_address,
            'status': self.status,
            'risk_level': self.risk_level,
            'call_sid': self.call_sid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if detailed:
            base.update({
                'blockchain_hash': self.blockchain_hash,
                'invoice_path': self.invoice_path,
                'human_approved_by': self.human_approved_by,
                'human_approved_at': self.human_approved_at.isoformat() if self.human_approved_at else None,
                'customer': self.customer.to_dict() if self.customer else None
            })
        
        return base

class CallSession(db.Model):
    """Call session tracking and transcript storage"""
    id = db.Column(db.Integer, primary_key=True)
    call_sid = db.Column(db.String(50), unique=True)
    order_id = db.Column(db.String(50))
    customer_phone = db.Column(db.String(20))
    detected_language = db.Column(db.String(10))
    intent_result = db.Column(db.String(20))  # YES / NO / UNKNOWN
    risk_decision = db.Column(db.String(20))
    retry_count = db.Column(db.Integer, default=0)
    duration_seconds = db.Column(db.Integer)
    full_transcript = db.Column(db.Text)  # JSON array of turns
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_sid': self.call_sid,
            'order_id': self.order_id,
            'customer_phone': self.customer_phone,
            'detected_language': self.detected_language,
            'intent_result': self.intent_result,
            'risk_decision': self.risk_decision,
            'retry_count': self.retry_count,
            'duration_seconds': self.duration_seconds,
            'full_transcript': json.loads(self.full_transcript) if self.full_transcript else [],
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None
        }

class AuditLog(db.Model):
    """Audit trail for all system events"""
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50))  # CALL_STARTED, ORDER_CONFIRMED, RISK_FLAGGED, etc.
    order_id = db.Column(db.String(50))
    call_sid = db.Column(db.String(50))
    actor = db.Column(db.String(100))  # 'ai_bot' / 'human:admin_name' / 'system'
    description = db.Column(db.Text)
    event_metadata = db.Column(db.Text)  # JSON - renamed to avoid SQLAlchemy conflict
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'order_id': self.order_id,
            'call_sid': self.call_sid,
            'actor': self.actor,
            'description': self.description,
            'metadata': json.loads(self.event_metadata) if self.event_metadata else {},
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

def log_audit(event_type: str, order_id: str, call_sid: str, actor: str, description: str, metadata: dict = None):
    """Helper function to log audit events"""
    audit = AuditLog(
        event_type=event_type,
        order_id=order_id,
        call_sid=call_sid,
        actor=actor,
        description=description,
        event_metadata=json.dumps(metadata) if metadata else None
    )
    db.session.add(audit)
    db.session.commit()