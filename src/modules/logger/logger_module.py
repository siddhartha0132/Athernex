"""Logger Module with comprehensive audit trail"""
import psycopg2
from datetime import datetime
from typing import List, Dict
import io

from src.event_bus.event_bus import EventBus, EventEnvelope
from src.storage.s3_client import S3Client


class LoggerModule:
    """Logs all events and records audio"""
    
    def __init__(
        self,
        event_bus: EventBus,
        postgres_url: str,
        s3_client: S3Client
    ):
        self.event_bus = event_bus
        self.postgres_conn = psycopg2.connect(postgres_url)
        self.s3_client = s3_client
        
        # Session buffers
        self.session_buffers: Dict[str, Dict] = {}
        
        # Subscribe to all events
        self.event_bus.subscribe_wildcard("*", self._handle_event)
    
    def _handle_event(self, envelope: EventEnvelope):
        """Handle all events for logging"""
        session_id = envelope.session_id
        event_type = envelope.event_type
        
        # Initialize session buffer if needed
        if session_id not in self.session_buffers:
            self.session_buffers[session_id] = {
                "audio_chunks": [],
                "transcripts": [],
                "state_transitions": [],
                "call_info": {},
                "start_time": datetime.utcnow()
            }
        
        buffer = self.session_buffers[session_id]
        
        # Handle specific event types
        if event_type == "call_connected":
            buffer["call_info"] = {
                "phone_number": envelope.data["phone_number"],
                "order_id": envelope.data["order_id"],
                "start_timestamp": envelope.timestamp
            }
            self._create_call_log(session_id, buffer["call_info"])
        
        elif event_type == "audio_input":
            # Buffer audio for recording
            buffer["audio_chunks"].append(envelope.data["audio_data"])
        
        elif event_type == "transcript_final":
            # Log transcript
            self._log_transcript(
                session_id,
                envelope.timestamp,
                "agent",
                envelope.data["transcript"],
                envelope.data["language"],
                envelope.data["confidence"]
            )
            buffer["transcripts"].append({
                "timestamp": envelope.timestamp,
                "speaker": "agent",
                "text": envelope.data["transcript"]
            })
        
        elif event_type == "llm_response_complete":
            # Log system response
            self._log_transcript(
                session_id,
                envelope.timestamp,
                "system",
                envelope.data["full_response"],
                None,
                None
            )
            buffer["transcripts"].append({
                "timestamp": envelope.timestamp,
                "speaker": "system",
                "text": envelope.data["full_response"]
            })
        
        elif event_type == "state_update":
            # Log state transition
            self._log_state_transition(
                session_id,
                envelope.timestamp,
                envelope.data.get("previous_state"),
                envelope.data["current_state"],
                envelope.data.get("transition_reason")
            )
            buffer["state_transitions"].append({
                "timestamp": envelope.timestamp,
                "from_state": envelope.data.get("previous_state"),
                "to_state": envelope.data["current_state"]
            })
        
        elif event_type == "call_ended":
            # Finalize call log
            self._finalize_call_log(
                session_id,
                envelope.timestamp,
                envelope.data["end_reason"],
                envelope.data.get("final_state")
            )
            
            # Upload audio recording
            if buffer["audio_chunks"]:
                self._upload_audio_recording(session_id, buffer["audio_chunks"], envelope.timestamp)
            
            # Cleanup buffer
            del self.session_buffers[session_id]
    
    def _create_call_log(self, session_id: str, call_info: Dict):
        """Create initial call log entry"""
        cursor = self.postgres_conn.cursor()
        
        cursor.execute("""
            INSERT INTO call_logs (session_id, phone_number, order_id, start_timestamp)
            VALUES (%s, %s, %s, %s)
        """, (
            session_id,
            call_info["phone_number"],
            call_info["order_id"],
            call_info["start_timestamp"]
        ))
        
        self.postgres_conn.commit()
        cursor.close()
    
    def _log_transcript(
        self,
        session_id: str,
        timestamp: str,
        speaker: str,
        text: str,
        language: str,
        confidence: float
    ):
        """Log transcript entry"""
        cursor = self.postgres_conn.cursor()
        
        cursor.execute("""
            INSERT INTO transcript_logs (session_id, timestamp, speaker, text, language, confidence)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session_id, timestamp, speaker, text, language, confidence))
        
        self.postgres_conn.commit()
        cursor.close()
    
    def _log_state_transition(
        self,
        session_id: str,
        timestamp: str,
        from_state: str,
        to_state: str,
        trigger_event: str
    ):
        """Log state transition"""
        cursor = self.postgres_conn.cursor()
        
        cursor.execute("""
            INSERT INTO state_transition_logs (session_id, timestamp, from_state, to_state, trigger_event)
            VALUES (%s, %s, %s, %s, %s)
        """, (session_id, timestamp, from_state, to_state, trigger_event))
        
        self.postgres_conn.commit()
        cursor.close()
    
    def _finalize_call_log(
        self,
        session_id: str,
        end_timestamp: str,
        end_reason: str,
        final_state: str
    ):
        """Update call log with end information"""
        cursor = self.postgres_conn.cursor()
        
        cursor.execute("""
            UPDATE call_logs
            SET end_timestamp = %s,
                end_reason = %s,
                final_state = %s
            WHERE session_id = %s
        """, (end_timestamp, end_reason, final_state, session_id))
        
        self.postgres_conn.commit()
        cursor.close()
    
    def _upload_audio_recording(
        self,
        session_id: str,
        audio_chunks: List[str],
        timestamp: str
    ):
        """Upload audio recording to S3"""
        # Combine audio chunks
        audio_bytes = b"".join(bytes.fromhex(chunk) for chunk in audio_chunks)
        
        # Upload to S3
        s3_url = self.s3_client.upload_audio(session_id, audio_bytes, timestamp)
        
        # Update call log with audio URL
        cursor = self.postgres_conn.cursor()
        cursor.execute("""
            UPDATE call_logs
            SET audio_file_url = %s
            WHERE session_id = %s
        """, (s3_url, session_id))
        
        self.postgres_conn.commit()
        cursor.close()
