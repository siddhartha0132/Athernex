"""Database initialization script"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

# SQL schema
SCHEMA_SQL = """
-- Call logs table
CREATE TABLE IF NOT EXISTS call_logs (
    session_id UUID PRIMARY KEY,
    phone_number VARCHAR(15) NOT NULL,
    order_id VARCHAR(50) NOT NULL,
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP,
    end_reason VARCHAR(50),
    final_state VARCHAR(50),
    detected_language VARCHAR(2),
    audio_file_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_logs_phone ON call_logs(phone_number);
CREATE INDEX IF NOT EXISTS idx_call_logs_order ON call_logs(order_id);
CREATE INDEX IF NOT EXISTS idx_call_logs_timestamp ON call_logs(start_timestamp);

-- Transcript logs table
CREATE TABLE IF NOT EXISTS transcript_logs (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES call_logs(session_id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    speaker VARCHAR(10) NOT NULL,
    text TEXT NOT NULL,
    language VARCHAR(2),
    confidence DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transcript_session ON transcript_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_transcript_timestamp ON transcript_logs(timestamp);

-- State transition logs table
CREATE TABLE IF NOT EXISTS state_transition_logs (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES call_logs(session_id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    from_state VARCHAR(50),
    to_state VARCHAR(50) NOT NULL,
    trigger_event TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_state_transition_session ON state_transition_logs(session_id);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    phone_number VARCHAR(15) PRIMARY KEY,
    preferred_language VARCHAR(2),
    name VARCHAR(100),
    typical_response_pattern TEXT,
    total_calls INTEGER DEFAULT 0,
    successful_confirmations INTEGER DEFAULT 0,
    last_call_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_prefs_phone ON user_preferences(phone_number);
"""

def init_database():
    """Initialize database schema"""
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        print("Error: POSTGRES_URL not set in environment")
        return
    
    try:
        conn = psycopg2.connect(postgres_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Creating database schema...")
        cursor.execute(SCHEMA_SQL)
        
        print("Database schema created successfully!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    init_database()
