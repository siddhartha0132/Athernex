"""System configuration management"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class LatencyBudgets(BaseSettings):
    """Latency budget configuration"""
    vad_detection: int = Field(default=200, alias="LATENCY_VAD_DETECTION")
    stt_final: int = Field(default=400, alias="LATENCY_STT_FINAL")
    llm_first_token: int = Field(default=800, alias="LATENCY_LLM_FIRST_TOKEN")
    tts_first_chunk: int = Field(default=300, alias="LATENCY_TTS_FIRST_CHUNK")
    total_target: int = Field(default=1800, alias="LATENCY_TOTAL_TARGET")


class RetryConfig(BaseSettings):
    """Retry policy configuration"""
    no_answer_max_attempts: int = Field(default=3, alias="RETRY_NO_ANSWER_MAX_ATTEMPTS")
    no_answer_initial_delay_min: int = Field(default=120, alias="RETRY_NO_ANSWER_INITIAL_DELAY_MIN")
    dropped_max_attempts: int = Field(default=3, alias="RETRY_DROPPED_MAX_ATTEMPTS")
    dropped_initial_delay_min: int = Field(default=30, alias="RETRY_DROPPED_INITIAL_DELAY_MIN")


class SystemConfig(BaseSettings):
    """Main system configuration"""
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_pool_size: int = Field(default=50, alias="REDIS_POOL_SIZE")
    
    # PostgreSQL
    postgres_url: str = Field(alias="POSTGRES_URL")
    
    # AWS S3
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    s3_bucket: str = Field(alias="S3_BUCKET")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    
    # Telephony
    twilio_account_sid: Optional[str] = Field(default=None, alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, alias="TWILIO_AUTH_TOKEN")
    twilio_webhook_url: Optional[str] = Field(default=None, alias="TWILIO_WEBHOOK_URL")
    exotel_api_key: Optional[str] = Field(default=None, alias="EXOTEL_API_KEY")
    exotel_api_token: Optional[str] = Field(default=None, alias="EXOTEL_API_TOKEN")
    
    # Google Cloud
    google_cloud_project: Optional[str] = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    google_application_credentials: Optional[str] = Field(default=None, alias="GOOGLE_APPLICATION_CREDENTIALS")
    
    # OpenAI
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    
    # Feature flags
    enable_dashboard: bool = Field(default=True, alias="ENABLE_DASHBOARD")
    enable_barge_in: bool = Field(default=True, alias="ENABLE_BARGE_IN")
    enable_audio_recording: bool = Field(default=True, alias="ENABLE_AUDIO_RECORDING")
    enable_preference_learning: bool = Field(default=True, alias="ENABLE_PREFERENCE_LEARNING")
    
    # Nested configs
    latency_budgets: LatencyBudgets = Field(default_factory=LatencyBudgets)
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global config instance
_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = SystemConfig()
    return _config
