"""STT Module with Google Cloud Speech-to-Text"""
from google.cloud import speech
from datetime import datetime
from typing import Optional, Dict
import time

from src.event_bus.event_bus import EventBus, EventEnvelope


class STTModule:
    """Speech-to-Text module with multi-language support"""
    
    def __init__(self, event_bus: EventBus, project_id: Optional[str] = None):
        self.event_bus = event_bus
        self.client = speech.SpeechClient()
        
        # Language models
        self.language_codes = {
            "hi": "hi-IN",
            "ta": "ta-IN",
            "kn": "kn-IN",
            "te": "te-IN",
            "mr": "mr-IN"
        }
        
        # Session state
        self.session_states: Dict[str, Dict] = {}
        
        # Subscribe to events
        self.event_bus.subscribe("processed_audio", self._handle_processed_audio)
        self.event_bus.subscribe("speech_ended", self._handle_speech_ended)
        self.event_bus.subscribe("preferences_loaded", self._handle_preferences_loaded)
    
    def _handle_processed_audio(self, envelope: EventEnvelope):
        """Process audio for transcription"""
        session_id = envelope.session_id
        
        # Initialize session if needed
        if session_id not in self.session_states:
            self.session_states[session_id] = {
                "audio_buffer": [],
                "detected_language": None,
                "preferred_language": None,
                "partial_transcript": ""
            }
        
        state = self.session_states[session_id]
        audio_hex = envelope.data["audio_data"]
        audio_bytes = bytes.fromhex(audio_hex)
        
        # Buffer audio
        state["audio_buffer"].append(audio_bytes)
        
        # Stream partial transcripts (every 10 chunks)
        if len(state["audio_buffer"]) % 10 == 0:
            self._generate_partial_transcript(session_id)
    
    def _handle_speech_ended(self, envelope: EventEnvelope):
        """Generate final transcript when speech ends"""
        session_id = envelope.session_id
        
        if session_id not in self.session_states:
            return
        
        state = self.session_states[session_id]
        
        # Combine buffered audio
        audio_data = b"".join(state["audio_buffer"])
        
        if not audio_data:
            return
        
        # Determine language
        language_code = self._determine_language(state)
        
        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language_code,
            enable_automatic_punctuation=True,
            model="latest_long"
        )
        
        audio = speech.RecognitionAudio(content=audio_data)
        
        # Perform recognition
        start_time = time.time()
        response = self.client.recognize(config=config, audio=audio)
        latency_ms = (time.time() - start_time) * 1000
        
        if response.results:
            result = response.results[0]
            transcript = result.alternatives[0].transcript
            confidence = result.alternatives[0].confidence
            
            # Detect language from result
            detected_lang = language_code.split("-")[0]
            if not state["detected_language"]:
                state["detected_language"] = detected_lang
            
            # Publish transcript_final event
            self.event_bus.publish(EventEnvelope(
                event_type="transcript_final",
                source_module="stt_module",
                session_id=session_id,
                data={
                    "transcript": transcript,
                    "language": detected_lang,
                    "confidence": confidence,
                    "duration_ms": int(latency_ms),
                    "alternatives": []
                }
            ))
        
        # Clear buffer
        state["audio_buffer"] = []
    
    def _generate_partial_transcript(self, session_id: str):
        """Generate partial transcript for streaming"""
        state = self.session_states[session_id]
        
        # Simplified - in production, use streaming recognition
        partial_text = f"[Partial transcript {len(state['audio_buffer'])} chunks]"
        
        self.event_bus.publish(EventEnvelope(
            event_type="transcript_partial",
            source_module="stt_module",
            session_id=session_id,
            data={
                "partial_transcript": partial_text,
                "confidence": 0.7,
                "is_final": False
            }
        ))
    
    def _determine_language(self, state: Dict) -> str:
        """Determine language for recognition"""
        # Use detected language if available
        if state["detected_language"]:
            return self.language_codes[state["detected_language"]]
        
        # Use preferred language if available
        if state["preferred_language"]:
            return self.language_codes[state["preferred_language"]]
        
        # Default to Hindi
        return self.language_codes["hi"]
    
    def _handle_preferences_loaded(self, envelope: EventEnvelope):
        """Load user's preferred language"""
        session_id = envelope.session_id
        preferred_lang = envelope.data.get("preferred_language")
        
        if session_id in self.session_states and preferred_lang:
            self.session_states[session_id]["preferred_language"] = preferred_lang
