"""LLM Module with OpenAI GPT-4 integration"""
from openai import OpenAI
from datetime import datetime
from typing import Dict, List, Optional
import time

from src.event_bus.event_bus import EventBus, EventEnvelope


class LLMModule:
    """LLM integration for response generation"""
    
    def __init__(self, event_bus: EventBus, api_key: str, model: str = "gpt-4"):
        self.event_bus = event_bus
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
        # Session context
        self.session_contexts: Dict[str, Dict] = {}
        
        # Subscribe to events
        self.event_bus.subscribe("transcript_final", self._handle_transcript)
        self.event_bus.subscribe("state_update", self._handle_state_update)
    
    def _handle_transcript(self, envelope: EventEnvelope):
        """Process transcript and generate response"""
        session_id = envelope.session_id
        transcript = envelope.data["transcript"]
        language = envelope.data["language"]
        
        # Initialize context if needed
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = {
                "conversation_history": [],
                "current_state": "greeting",
                "language": language,
                "order_details": {}
            }
        
        context = self.session_contexts[session_id]
        context["language"] = language
        
        # Add to conversation history (keep last 3 turns)
        context["conversation_history"].append({
            "role": "user",
            "content": transcript
        })
        if len(context["conversation_history"]) > 6:  # 3 turns = 6 messages
            context["conversation_history"] = context["conversation_history"][-6:]
        
        # Generate response
        self._generate_response(session_id)
    
    def _handle_state_update(self, envelope: EventEnvelope):
        """Update conversation state"""
        session_id = envelope.session_id
        
        if session_id in self.session_contexts:
            self.session_contexts[session_id]["current_state"] = envelope.data["current_state"]
    
    def _generate_response(self, session_id: str):
        """Generate LLM response"""
        context = self.session_contexts[session_id]
        
        # Build system prompt
        system_prompt = self._build_system_prompt(context)
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt}
        ] + context["conversation_history"]
        
        # Stream response
        start_time = time.time()
        first_token_time = None
        full_response = ""
        token_sequence = 0
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=50,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    
                    if first_token_time is None:
                        first_token_time = time.time()
                        latency_ms = (first_token_time - start_time) * 1000
                        print(f"First token latency: {latency_ms}ms")
                    
                    # Publish token
                    self.event_bus.publish(EventEnvelope(
                        event_type="llm_response_token",
                        source_module="llm_module",
                        session_id=session_id,
                        data={
                            "token": token,
                            "token_sequence": token_sequence,
                            "is_final": False
                        }
                    ))
                    token_sequence += 1
            
            # Publish completion
            generation_time = (time.time() - start_time) * 1000
            self.event_bus.publish(EventEnvelope(
                event_type="llm_response_complete",
                source_module="llm_module",
                session_id=session_id,
                data={
                    "full_response": full_response,
                    "token_count": token_sequence,
                    "generation_time_ms": int(generation_time),
                    "model_used": self.model
                }
            ))
            
            # Add to history
            context["conversation_history"].append({
                "role": "assistant",
                "content": full_response
            })
            
        except Exception as e:
            print(f"Error generating response: {e}")
    
    def _build_system_prompt(self, context: Dict) -> str:
        """Build system prompt based on context"""
        language = context["language"]
        state = context["current_state"]
        
        # Language-specific greetings
        greetings = {
            "hi": "Namaste",
            "ta": "Vanakkam",
            "kn": "Namaskara",
            "te": "Namaskaram",
            "mr": "Namaskar"
        }
        
        greeting = greetings.get(language, "Namaste")
        
        prompt = f"""You are a polite order confirmation agent for an Indian delivery service.
Language: {language}
Current state: {state}
Greeting: {greeting}

Rules:
- Keep responses under 20 words
- Always use "ji" suffix when addressing the agent
- Be polite and respectful
- Confirm order details clearly
- If unclear, ask for clarification

Respond naturally in {language}."""
        
        return prompt
