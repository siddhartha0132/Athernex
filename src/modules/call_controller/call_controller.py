"""Call Controller with retry logic"""
from celery import Celery
from datetime import datetime, timedelta
from typing import Dict, Optional

from src.event_bus.event_bus import EventBus, EventEnvelope


class CallController:
    """Manages call lifecycle and retry logic"""
    
    def __init__(
        self,
        event_bus: EventBus,
        celery_app: Celery,
        retry_config: Dict
    ):
        self.event_bus = event_bus
        self.celery_app = celery_app
        self.retry_config = retry_config
        
        # Track call attempts
        self.call_attempts: Dict[str, Dict] = {}
        
        # Subscribe to events
        self.event_bus.subscribe("call_ended", self._handle_call_ended)
        self.event_bus.subscribe("state_update", self._handle_state_update)
    
    def _handle_call_ended(self, envelope: EventEnvelope):
        """Handle call end and schedule retries if needed"""
        session_id = envelope.session_id
        phone_number = envelope.data["phone_number"]
        order_id = envelope.data["order_id"]
        end_reason = envelope.data["end_reason"]
        final_state = envelope.data.get("final_state", "unknown")
        
        # Track attempt
        call_key = f"{phone_number}:{order_id}"
        if call_key not in self.call_attempts:
            self.call_attempts[call_key] = {
                "attempts": 0,
                "last_session_id": session_id
            }
        
        self.call_attempts[call_key]["attempts"] += 1
        attempts = self.call_attempts[call_key]["attempts"]
        
        # Determine if retry is needed
        should_retry, delay_minutes = self._should_retry(
            end_reason,
            final_state,
            attempts
        )
        
        if should_retry:
            # Schedule retry
            scheduled_time = datetime.utcnow() + timedelta(minutes=delay_minutes)
            
            self.event_bus.publish(EventEnvelope(
                event_type="retry_scheduled",
                source_module="call_controller",
                session_id=session_id,
                data={
                    "phone_number": phone_number,
                    "order_id": order_id,
                    "attempt_number": attempts + 1,
                    "scheduled_time": scheduled_time.isoformat(),
                    "retry_reason": end_reason,
                    "previous_session_id": session_id
                }
            ))
            
            # Schedule Celery task
            self._schedule_retry_task(
                phone_number,
                order_id,
                attempts + 1,
                delay_minutes
            )
    
    def _handle_state_update(self, envelope: EventEnvelope):
        """Track terminal states"""
        current_state = envelope.data["current_state"]
        
        # Terminal states don't need retry tracking
        if current_state in ["confirmed", "rejected"]:
            # Could cleanup call_attempts here
            pass
    
    def _should_retry(
        self,
        end_reason: str,
        final_state: str,
        attempts: int
    ) -> tuple[bool, int]:
        """Determine if call should be retried"""
        # No retry for terminal states
        if final_state in ["confirmed", "rejected"]:
            return False, 0
        
        # No answer retry policy
        if end_reason == "no_answer":
            max_attempts = self.retry_config["no_answer_max_attempts"]
            if attempts >= max_attempts:
                return False, 0
            
            initial_delay = self.retry_config["no_answer_initial_delay_min"]
            delay = int(initial_delay * (1.5 ** (attempts - 1)))
            return True, delay
        
        # Dropped call retry policy
        if end_reason == "dropped":
            max_attempts = self.retry_config["dropped_max_attempts"]
            if attempts >= max_attempts:
                return False, 0
            
            initial_delay = self.retry_config["dropped_initial_delay_min"]
            delay = int(initial_delay * (2.0 ** (attempts - 1)))
            return True, delay
        
        # Error retry policy
        if end_reason == "error":
            if attempts >= 2:
                return False, 0
            
            delay = 5 * (3 ** (attempts - 1))
            return True, delay
        
        return False, 0
    
    def _schedule_retry_task(
        self,
        phone_number: str,
        order_id: str,
        attempt_number: int,
        delay_minutes: int
    ):
        """Schedule retry using Celery"""
        # In production, this would schedule a Celery task
        # For now, just log
        print(f"Scheduling retry for {phone_number} in {delay_minutes} minutes (attempt {attempt_number})")
