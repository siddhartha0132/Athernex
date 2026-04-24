# AI Voice Order Confirmation System

Real-time AI voice operating system for delivery agent order confirmation calls in Hindi and regional Indian languages.

## Architecture

Event-driven system with 10 modules communicating via Redis Event Bus:
- Telephony Module (Twilio/Exotel)
- Audio Processor (VAD + Noise Reduction)
- STT Module (Multi-language)
- LLM Module (Response Generation)
- State Machine (Conversation Flow)
- TTS Module (Multi-language)
- Dashboard (Real-time Monitoring)
- Call Controller (Retry Logic)
- Session Store (User Preferences)
- Logger (Audit Trail)

## Setup

```bash
# Install dependencies
pip install -e .

# Copy environment template
cp .env.example .env

# Edit .env with your credentials

# Run database migrations
python scripts/init_db.py

# Start services
docker-compose up -d
```

## Development

```bash
# Run tests
pytest

# Run property tests
pytest tests/property_tests/

# Start development server
python -m src.main
```

## Latency Budget

- VAD detection: < 200ms
- STT final: < 400ms
- LLM first token: < 800ms
- TTS first chunk: < 300ms
- **Total: < 1.8s**
# Athernex
