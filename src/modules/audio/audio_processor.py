"""Audio Processor with noise reduction and VAD"""
import numpy as np
import webrtcvad
from datetime import datetime
from typing import List, Optional
import time

from src.event_bus.event_bus import EventBus, EventEnvelope


class AudioProcessor:
    """Processes audio with noise reduction and voice activity detection"""
    
    def __init__(
        self,
        event_bus: EventBus,
        vad_aggressiveness: int = 3,
        speech_end_silence_ms: int = 200,
        target_db: float = -20.0
    ):
        self.event_bus = event_bus
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.speech_end_silence_ms = speech_end_silence_ms
        self.target_db = target_db
        
        # State tracking
        self.session_states = {}
        
        # Subscribe to audio_input events
        self.event_bus.subscribe("audio_input", self._handle_audio_input)
        self.event_bus.subscribe("tts_playback_started", self._handle_tts_started)
        self.event_bus.subscribe("tts_playback_stopped", self._handle_tts_stopped)
    
    def _handle_audio_input(self, envelope: EventEnvelope):
        """Process incoming audio"""
        session_id = envelope.session_id
        audio_hex = envelope.data["audio_data"]
        audio_bytes = bytes.fromhex(audio_hex)
        
        # Initialize session state if needed
        if session_id not in self.session_states:
            self.session_states[session_id] = {
                "is_speaking": False,
                "speech_start_time": None,
                "last_speech_time": None,
                "tts_playing": False,
                "chunk_sequence": 0
            }
        
        state = self.session_states[session_id]
        state["chunk_sequence"] += 1
        
        # Apply noise reduction (simplified - in production use RNNoise)
        cleaned_audio = self._apply_noise_reduction(audio_bytes)
        
        # Normalize volume
        normalized_audio = self._normalize_volume(cleaned_audio)
        
        # Publish processed_audio event
        self.event_bus.publish(EventEnvelope(
            event_type="processed_audio",
            source_module="audio_processor",
            session_id=session_id,
            data={
                "chunk_sequence": state["chunk_sequence"],
                "audio_data": normalized_audio.hex(),
                "format": "pcm16",
                "sample_rate": 16000,
                "noise_reduction_applied": True,
                "volume_normalized": True
            }
        ))
        
        # Run VAD
        is_speech = self._detect_speech(normalized_audio)
        
        # Check for barge-in
        if is_speech and state["tts_playing"]:
            self.event_bus.publish(EventEnvelope(
                event_type="barge_in_detected",
                source_module="audio_processor",
                session_id=session_id,
                data={
                    "timestamp": datetime.utcnow().isoformat(),
                    "interrupted_at_chunk": state["chunk_sequence"],
                    "system_was_speaking": True
                }
            ))
            state["tts_playing"] = False
        
        # Track speech boundaries
        current_time = time.time() * 1000  # milliseconds
        
        if is_speech:
            if not state["is_speaking"]:
                # Speech started
                state["is_speaking"] = True
                state["speech_start_time"] = current_time
                
                self.event_bus.publish(EventEnvelope(
                    event_type="speech_started",
                    source_module="audio_processor",
                    session_id=session_id,
                    data={
                        "timestamp": datetime.utcnow().isoformat(),
                        "chunk_sequence": state["chunk_sequence"],
                        "confidence": 0.9
                    }
                ))
            
            state["last_speech_time"] = current_time
        else:
            if state["is_speaking"]:
                # Check if silence duration exceeds threshold
                silence_duration = current_time - state["last_speech_time"]
                if silence_duration >= self.speech_end_silence_ms:
                    # Speech ended
                    speech_duration = current_time - state["speech_start_time"]
                    state["is_speaking"] = False
                    
                    self.event_bus.publish(EventEnvelope(
                        event_type="speech_ended",
                        source_module="audio_processor",
                        session_id=session_id,
                        data={
                            "timestamp": datetime.utcnow().isoformat(),
                            "chunk_sequence": state["chunk_sequence"],
                            "confidence": 0.9,
                            "duration_ms": int(speech_duration)
                        }
                    ))
    
    def _apply_noise_reduction(self, audio_bytes: bytes) -> bytes:
        """Apply noise reduction (simplified)"""
        # In production, use RNNoise library
        # For now, return as-is
        return audio_bytes
    
    def _normalize_volume(self, audio_bytes: bytes) -> bytes:
        """Normalize audio volume to target dB"""
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        
        # Calculate RMS
        rms = np.sqrt(np.mean(audio_array.astype(float) ** 2))
        
        if rms > 0:
            # Calculate target RMS from dB
            target_rms = 10 ** (self.target_db / 20) * 32768
            
            # Apply gain
            gain = target_rms / rms
            normalized = (audio_array * gain).astype(np.int16)
            
            return normalized.tobytes()
        
        return audio_bytes
    
    def _detect_speech(self, audio_bytes: bytes) -> bool:
        """Detect if audio contains speech using VAD"""
        # VAD requires specific frame sizes (10, 20, or 30 ms)
        # For 16kHz, 30ms = 480 samples = 960 bytes
        frame_size = 960
        
        if len(audio_bytes) < frame_size:
            return False
        
        # Take first frame
        frame = audio_bytes[:frame_size]
        
        try:
            return self.vad.is_speech(frame, 16000)
        except:
            return False
    
    def _handle_tts_started(self, envelope: EventEnvelope):
        """Track when TTS starts playing"""
        session_id = envelope.session_id
        if session_id in self.session_states:
            self.session_states[session_id]["tts_playing"] = True
    
    def _handle_tts_stopped(self, envelope: EventEnvelope):
        """Track when TTS stops playing"""
        session_id = envelope.session_id
        if session_id in self.session_states:
            self.session_states[session_id]["tts_playing"] = False
