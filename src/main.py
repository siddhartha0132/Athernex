"""Main application entry point"""
import asyncio
from src.config.system_config import get_config
from src.event_bus.event_bus import EventBus
from src.storage.s3_client import S3Client
from src.modules.telephony.telephony_module import TelephonyModule
from src.modules.audio.audio_processor import AudioProcessor
from src.modules.stt.stt_module import STTModule
from src.modules.llm.llm_module import LLMModule
from src.modules.state.state_machine import StateManager
from src.modules.tts.tts_module import TTSModule
from src.modules.call_controller.call_controller import CallController
from src.modules.session_store.session_store import SessionStore
from src.modules.logger.logger_module import LoggerModule


def main():
    """Initialize and start the system"""
    print("Starting AI Voice Order Confirmation System...")
    
    # Load configuration
    config = get_config()
    
    # Initialize Event Bus
    event_bus = EventBus(
        redis_url=config.redis_url,
        pool_size=config.redis_pool_size
    )
    
    # Initialize S3 Client
    s3_client = S3Client(
        bucket_name=config.s3_bucket,
        region=config.s3_region,
        access_key=config.aws_access_key_id,
        secret_key=config.aws_secret_access_key
    )
    
    # Initialize modules
    print("Initializing modules...")
    
    telephony = TelephonyModule(
        event_bus=event_bus,
        account_sid=config.twilio_account_sid,
        auth_token=config.twilio_auth_token,
        webhook_url=config.twilio_webhook_url
    )
    
    audio_processor = AudioProcessor(event_bus=event_bus)
    
    stt_module = STTModule(
        event_bus=event_bus,
        project_id=config.google_cloud_project
    )
    
    llm_module = LLMModule(
        event_bus=event_bus,
        api_key=config.openai_api_key,
        model=config.openai_model
    )
    
    state_manager = StateManager(event_bus=event_bus)
    
    tts_module = TTSModule(event_bus=event_bus)
    
    session_store = SessionStore(
        event_bus=event_bus,
        postgres_url=config.postgres_url,
        redis_url=config.redis_url
    )
    
    call_controller = CallController(
        event_bus=event_bus,
        celery_app=None,  # Initialize Celery separately
        retry_config={
            "no_answer_max_attempts": config.retry_config.no_answer_max_attempts,
            "no_answer_initial_delay_min": config.retry_config.no_answer_initial_delay_min,
            "dropped_max_attempts": config.retry_config.dropped_max_attempts,
            "dropped_initial_delay_min": config.retry_config.dropped_initial_delay_min
        }
    )
    
    logger_module = LoggerModule(
        event_bus=event_bus,
        postgres_url=config.postgres_url,
        s3_client=s3_client
    )
    
    print("All modules initialized successfully!")
    print("System ready to handle calls.")
    print(f"Latency budget: {config.latency_budgets.total_target}ms")
    
    # Start event bus listener
    try:
        event_bus.start_listening()
    except KeyboardInterrupt:
        print("\nShutting down...")
        event_bus.stop_listening()


if __name__ == "__main__":
    main()
