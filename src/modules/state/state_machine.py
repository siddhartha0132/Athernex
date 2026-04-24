"""State Machine for conversation flow"""
from statemachine import StateMachine as SM, State
from datetime import datetime
from typing import Dict, Optional

from src.event_bus.event_bus import EventBus, EventEnvelope


class ConversationStateMachine(SM):
    """State machine for call conversation flow"""
    
    # Define states
    greeting = State(initial=True)
    awaiting_confirmation = State()
    clarification = State()
    confirmed = State(final=True)
    rejected = State(final=True)
    escalate = State(final=True)
    
    # Define transitions
    greeting_complete = greeting.to(awaiting_confirmation)
    confirmation_detected = awaiting_confirmation.to(confirmed)
    rejection_detected = awaiting_confirmation.to(rejected)
    clarification_needed = awaiting_confirmation.to(clarification)
    clarification_provided = clarification.to(awaiting_confirmation)
    max_clarifications_reached = clarification.to(escalate)
    
    def __init__(self, session_id: str, event_bus: EventBus):
        super().__init__()
        self.session_id = session_id
        self.event_bus = event_bus
        self.clarification_count = 0
    
    def on_transition(self, event, source, target):
        """Publish state_update event on every transition"""
        self.event_bus.publish(EventEnvelope(
            event_type="state_update",
            source_module="state_machine",
            session_id=self.session_id,
            data={
                "previous_state": source.id,
                "current_state": target.id,
                "transition_reason": event,
                "state_data": {
                    "clarification_attempts": self.clarification_count
                }
            }
        ))


class StateManager:
    """Manages state machines for all sessions"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.state_machines: Dict[str, ConversationStateMachine] = {}
        
        # Subscribe to events
        self.event_bus.subscribe("call_connected", self._handle_call_connected)
        self.event_bus.subscribe("transcript_final", self._handle_transcript)
        self.event_bus.subscribe("llm_response_complete", self._handle_llm_complete)
    
    def _handle_call_connected(self, envelope: EventEnvelope):
        """Initialize state machine for new call"""
        session_id = envelope.session_id
        
        # Create state machine
        sm = ConversationStateMachine(session_id, self.event_bus)
        self.state_machines[session_id] = sm
        
        # Publish initial state
        self.event_bus.publish(EventEnvelope(
            event_type="state_update",
            source_module="state_machine",
            session_id=session_id,
            data={
                "previous_state": None,
                "current_state": "greeting",
                "transition_reason": "call_connected",
                "state_data": {}
            }
        ))
    
    def _handle_transcript(self, envelope: EventEnvelope):
        """Analyze transcript for state transitions"""
        session_id = envelope.session_id
        transcript = envelope.data["transcript"].lower()
        confidence = envelope.data["confidence"]
        
        if session_id not in self.state_machines:
            return
        
        sm = self.state_machines[session_id]
        
        # Detect intent
        intent, intent_confidence = self._detect_intent(transcript)
        
        # Only transition on high confidence
        if intent_confidence < 0.7:
            return
        
        # Handle transitions based on current state
        if sm.current_state == sm.awaiting_confirmation:
            if intent == "confirm":
                sm.confirmation_detected()
            elif intent == "reject":
                sm.rejection_detected()
            elif intent == "unclear":
                sm.clarification_count += 1
                if sm.clarification_count >= 3:
                    sm.max_clarifications_reached()
                else:
                    sm.clarification_needed()
        
        elif sm.current_state == sm.clarification:
            if intent in ["confirm", "reject", "clarify"]:
                sm.clarification_provided()
    
    def _handle_llm_complete(self, envelope: EventEnvelope):
        """Track conversation progress"""
        session_id = envelope.session_id
        response = envelope.data["full_response"].lower()
        
        if session_id not in self.state_machines:
            return
        
        sm = self.state_machines[session_id]
        
        # If in greeting state and greeting is complete, transition
        if sm.current_state == sm.greeting:
            if any(word in response for word in ["confirm", "order", "delivery"]):
                sm.greeting_complete()
    
    def _detect_intent(self, transcript: str) -> tuple[str, float]:
        """Detect intent from transcript"""
        # Simplified intent detection
        # In production, use more sophisticated NLP
        
        # Confirmation keywords
        confirm_keywords = ["yes", "haan", "sahi", "theek", "correct", "ok", "confirm"]
        if any(word in transcript for word in confirm_keywords):
            return "confirm", 0.9
        
        # Rejection keywords
        reject_keywords = ["no", "nahi", "cancel", "wrong", "galat"]
        if any(word in transcript for word in reject_keywords):
            return "reject", 0.9
        
        # Unclear
        return "unclear", 0.5
