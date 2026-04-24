"""Event Bus implementation with Redis Pub/Sub"""
import json
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import redis
from redis.client import PubSub


class EventEnvelope:
    """Standardized event envelope"""
    
    def __init__(
        self,
        event_type: str,
        source_module: str,
        session_id: str,
        data: Dict[str, Any],
        event_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        version: str = "1.0"
    ):
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.source_module = source_module
        self.session_id = session_id
        self.data = data
        self.version = version
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "source_module": self.source_module,
            "session_id": self.session_id,
            "data": self.data,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventEnvelope":
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            timestamp=data["timestamp"],
            source_module=data["source_module"],
            session_id=data["session_id"],
            data=data["data"],
            version=data.get("version", "1.0")
        )
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate event envelope structure"""
        required_fields = ["event_id", "event_type", "timestamp", "source_module", "session_id", "version"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"
        return True, None


class EventBus:
    """Central event bus using Redis Pub/Sub"""
    
    def __init__(self, redis_url: str, pool_size: int = 50):
        self.redis_client = redis.from_url(
            redis_url,
            max_connections=pool_size,
            decode_responses=True
        )
        self.pubsub: Optional[PubSub] = None
        self.subscribers: Dict[str, List[Callable]] = {}
    
    def publish(self, envelope: EventEnvelope) -> None:
        """Publish event to the bus"""
        # Validate envelope
        event_dict = envelope.to_dict()
        is_valid, error = EventEnvelope.validate(event_dict)
        if not is_valid:
            raise ValueError(f"Invalid event envelope: {error}")
        
        # Publish to Redis channel
        channel = f"events:{envelope.event_type}"
        message = json.dumps(event_dict)
        self.redis_client.publish(channel, message)
    
    def subscribe(self, event_type: str, callback: Callable[[EventEnvelope], None]) -> None:
        """Subscribe to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def subscribe_wildcard(self, pattern: str, callback: Callable[[EventEnvelope], None]) -> None:
        """Subscribe to events matching pattern"""
        if pattern not in self.subscribers:
            self.subscribers[pattern] = []
        self.subscribers[pattern].append(callback)
    
    def start_listening(self) -> None:
        """Start listening for events"""
        if self.pubsub is None:
            self.pubsub = self.redis_client.pubsub()
        
        # Subscribe to all registered event types
        for event_type in self.subscribers.keys():
            if "*" in event_type:
                self.pubsub.psubscribe(f"events:{event_type}")
            else:
                self.pubsub.subscribe(f"events:{event_type}")
        
        # Listen for messages
        for message in self.pubsub.listen():
            if message["type"] in ["message", "pmessage"]:
                self._handle_message(message["data"])
    
    def _handle_message(self, message_data: str) -> None:
        """Handle incoming message"""
        try:
            event_dict = json.loads(message_data)
            envelope = EventEnvelope.from_dict(event_dict)
            
            # Call all subscribers for this event type
            if envelope.event_type in self.subscribers:
                for callback in self.subscribers[envelope.event_type]:
                    callback(envelope)
            
            # Call wildcard subscribers
            for pattern, callbacks in self.subscribers.items():
                if "*" in pattern and self._matches_pattern(envelope.event_type, pattern):
                    for callback in callbacks:
                        callback(envelope)
        except Exception as e:
            print(f"Error handling message: {e}")
    
    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches wildcard pattern"""
        import re
        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(regex_pattern, event_type))
    
    def stop_listening(self) -> None:
        """Stop listening for events"""
        if self.pubsub:
            self.pubsub.close()
            self.pubsub = None
