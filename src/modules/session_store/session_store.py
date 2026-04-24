"""Session Store with PostgreSQL and Redis caching"""
import json
from datetime import datetime
from typing import Dict, Optional
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

from src.event_bus.event_bus import EventBus, EventEnvelope


class SessionStore:
    """Manages user preferences and session data"""
    
    def __init__(
        self,
        event_bus: EventBus,
        postgres_url: str,
        redis_url: str,
        cache_ttl: int = 86400  # 24 hours
    ):
        self.event_bus = event_bus
        self.postgres_conn = psycopg2.connect(postgres_url)
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.cache_ttl = cache_ttl
        
        # Subscribe to events
        self.event_bus.subscribe("call_connected", self._handle_call_connected)
        self.event_bus.subscribe("call_ended", self._handle_call_ended)
        self.event_bus.subscribe("transcript_final", self._handle_transcript)
    
    def _handle_call_connected(self, envelope: EventEnvelope):
        """Load preferences when call connects"""
        session_id = envelope.session_id
        phone_number = envelope.data["phone_number"]
        
        # Load preferences
        preferences = self.get_preferences(phone_number)
        
        # Publish preferences_loaded event
        self.event_bus.publish(EventEnvelope(
            event_type="preferences_loaded",
            source_module="session_store",
            session_id=session_id,
            data={
                "phone_number": phone_number,
                "preferred_language": preferences.get("preferred_language"),
                "name": preferences.get("name"),
                "interaction_history": {
                    "total_calls": preferences.get("total_calls", 0),
                    "successful_confirmations": preferences.get("successful_confirmations", 0),
                    "typical_response_pattern": preferences.get("typical_response_pattern")
                }
            }
        ))
    
    def _handle_call_ended(self, envelope: EventEnvelope):
        """Update preferences when call ends"""
        session_id = envelope.session_id
        phone_number = envelope.data["phone_number"]
        final_state = envelope.data.get("final_state")
        
        # Update call statistics
        cursor = self.postgres_conn.cursor()
        
        if final_state == "confirmed":
            cursor.execute("""
                UPDATE user_preferences
                SET total_calls = total_calls + 1,
                    successful_confirmations = successful_confirmations + 1,
                    last_call_timestamp = %s,
                    updated_at = NOW()
                WHERE phone_number = %s
            """, (datetime.utcnow(), phone_number))
        else:
            cursor.execute("""
                UPDATE user_preferences
                SET total_calls = total_calls + 1,
                    last_call_timestamp = %s,
                    updated_at = NOW()
                WHERE phone_number = %s
            """, (datetime.utcnow(), phone_number))
        
        self.postgres_conn.commit()
        cursor.close()
        
        # Invalidate cache
        cache_key = f"preferences:{phone_number}"
        self.redis_client.delete(cache_key)
    
    def _handle_transcript(self, envelope: EventEnvelope):
        """Track interaction patterns"""
        # Could analyze transcripts to learn typical response patterns
        pass
    
    def get_preferences(self, phone_number: str) -> Dict:
        """Get user preferences with caching"""
        # Check cache first
        cache_key = f"preferences:{phone_number}"
        cached = self.redis_client.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # Query database
        cursor = self.postgres_conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM user_preferences WHERE phone_number = %s
        """, (phone_number,))
        
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            preferences = dict(result)
            
            # Cache result
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(preferences, default=str)
            )
            
            return preferences
        
        # No preferences found, return empty
        return {}
    
    def save_preferences(
        self,
        phone_number: str,
        language: Optional[str] = None,
        name: Optional[str] = None,
        interaction_pattern: Optional[str] = None
    ):
        """Save or update user preferences"""
        cursor = self.postgres_conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_preferences (phone_number, preferred_language, name, typical_response_pattern)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (phone_number)
            DO UPDATE SET
                preferred_language = COALESCE(EXCLUDED.preferred_language, user_preferences.preferred_language),
                name = COALESCE(EXCLUDED.name, user_preferences.name),
                typical_response_pattern = COALESCE(EXCLUDED.typical_response_pattern, user_preferences.typical_response_pattern),
                updated_at = NOW()
        """, (phone_number, language, name, interaction_pattern))
        
        self.postgres_conn.commit()
        cursor.close()
        
        # Invalidate cache
        cache_key = f"preferences:{phone_number}"
        self.redis_client.delete(cache_key)
