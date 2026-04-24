"""TTS Module with Google Cloud Text-to-Speech"""
from google.cloud import texttospeech
from datetime import datetime
from typing import Dict, Optional
import time

from src.event_bus.event_bus import EventBus, EventEnvelope


class TTSModule:
    """Text-to-Speech synthesis module"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.client = texttospeech.TextToSpeechClient()
        
        # Voice mapping
        self.voice_map = {
            "hi": "hi-IN-Wavenet-D",
            "ta": "ta-IN-Wavenet-A",
            "kn": "kn-IN-Wavenet-A",
            "te": "te-IN-Wavenet-B",
            "mr": "mr-IN-Wavenet-A"
        }
        
        # Pre-rendered audio cache
        self.audio_cache: Dict[str, bytes] = {}
        
        # Session state
        self.session_states: Dict[str, Dict] = {}
        
        # Subscribe to events
        self.event_bus.subscribe("llm_response_token", self._handle_response_token)
        self.event_bus.subscribe("state_update", self._handle_state_update)
        self.event_bus.subscribe("barge_in_detected", self._handle_barge_in)
    
    def _handle_response_token(self, envelope: EventEnvelope):
        """Handle streaming response tokens"""
        session_id = envelope.session_id
        token = envelope.data["token"]
        is_final = envelope.data["is_final"]
        
        # Initialize session if needed
        if session_id not in self.session_states:
            self.session_states[session_id] = {
                "text_buffer": "",
                "language": "hi",
                "is_playing": False
            }
        
        state = self.session_states[session_id]
        state["text_buffer"] += token
        
        # Synthesize when we have a complete sentence or final token
        if "." in state["text_buffer"] or "?" in state["text_buffer"] or is_final:
            self._synthesize_and_stream(session_id)
    
    def _handle_state_update(self, envelope: EventEnvelope):
        """Handle state updates for pre-rendered audio"""
        session_id = envelope.session_id
        current_state = envelope.data["current_state"]
        
        # Check for pre-rendered audio opportunities
        if current_state == "confirmed":
            self._play_cached_audio(session_id, "ORDER_CONFIRMED")
    
    def _handle_barge_in(self, envelope: EventEnvelope):
        """Stop playback on barge-in"""
        session_id = envelope.session_id
        
        if session_id in self.session_states:
            state = self.session_states[session_id]
            if state["is_playing"]:
                state["is_playing"] = False
                state["text_buffer"] = ""
                
                # Publish playback stopped
                self.event_bus.publish(EventEnvelope(
                    event_type="tts_playback_stopped",
                    source_module="tts_module",
                    session_id=session_id,
                    data={
                        "text": "",
                        "language": state["language"],
                        "voice_id": self.voice_map[state["language"]],
                        "reason": "barge_in"
                    }
                ))
    
    def _synthesize_and_stream(self, session_id: str):
        """Synthesize text and stream audio"""
        state = self.session_states[session_id]
        text = state["text_buffer"].strip()
        
        if not text:
            return
        
        language = state["language"]
        voice_id = self.voice_map.get(language, self.voice_map["hi"])
        
        # Check cache first
        cache_key = f"{language}:{text}"
        if cache_key in self.audio_cache:
            audio_data = self.audio_cache[cache_key]
            self._stream_audio(session_id, audio_data, text, language, voice_id, cached=True)
            state["text_buffer"] = ""
            return
        
        # Synthesize
        start_time = time.time()
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language + "-IN",
            name=voice_id
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000
        )
        
        try:
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            latency_ms = (time.time() - start_time) * 1000
            print(f"TTS synthesis latency: {latency_ms}ms")
            
            audio_data = response.audio_content
            
            # Cache if common phrase
            if len(text) < 50:
                self.audio_cache[cache_key] = audio_data
            
            # Stream audio
            self._stream_audio(session_id, audio_data, text, language, voice_id, cached=False)
            
        except Exception as e:
            print(f"Error synthesizing speech: {e}")
        
        state["text_buffer"] = ""
    
    def _stream_audio(
        self,
        session_id: str,
        audio_data: bytes,
        text: str,
        language: str,
        voice_id: str,
        cached: bool
    ):
        """Stream audio to telephony"""
        state = self.session_states[session_id]
        state["is_playing"] = True
        
        # Publish playback started
        self.event_bus.publish(EventEnvelope(
            event_type="tts_playback_started",
            source_module="tts_module",
            session_id=session_id,
            data={
                "text": text,
                "language": language,
                "voice_id": voice_id,
                "estimated_duration_ms": len(audio_data) // 32  # Rough estimate
            }
        ))
        
        # Stream audio in chunks
        chunk_size = 3200  # 100ms at 16kHz
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            
            self.event_bus.publish(EventEnvelope(
                event_type="audio_output",
                source_module="tts_module",
                session_id=session_id,
                data={
                    "chunk_sequence": i // chunk_size,
                    "audio_data": chunk.hex(),
                    "format": "pcm16",
                    "sample_rate": 16000,
                    "duration_ms": 100,
                    "is_final": i + chunk_size >= len(audio_data)
                }
            ))
        
        # Publish playback stopped
        state["is_playing"] = False
        self.event_bus.publish(EventEnvelope(
            event_type="tts_playback_stopped",
            source_module="tts_module",
            session_id=session_id,
            data={
                "text": text,
                "language": language,
                "voice_id": voice_id
            }
        ))
    
    def _play_cached_audio(self, session_id: str, alert_key: str):
        """Play pre-rendered audio clip"""
        # In production, load from pre-rendered files
        pass
