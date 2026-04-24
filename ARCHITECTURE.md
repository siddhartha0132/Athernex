# 🏗️ System Architecture

Complete technical architecture of the AI Voice Call System.

---

## 📊 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CALL FLOW                               │
└─────────────────────────────────────────────────────────────────┘

1. CALL INITIATION
   User → Twilio Number → Twilio Cloud → /voice webhook

2. GREETING & RECORDING
   Flask → TwiML Response → Twilio → Plays greeting → Records audio

3. AUDIO PROCESSING
   Twilio → /process webhook → Flask downloads audio

4. SPEECH-TO-TEXT
   Flask → Sarvam AI STT API → Transcript

5. LLM PROCESSING
   Flask → Local Ollama → AI Response

6. TEXT-TO-SPEECH
   Flask → Sarvam AI TTS API → Audio file

7. RESPONSE PLAYBACK
   Flask → TwiML with <Play> → Twilio → Plays to user

8. LOOP
   Back to step 2 (recording next input)

9. CLEANUP
   Call ends → /call-status → Delete audio files & history
```

---

## 🔧 Component Details

### 1. Flask Application (app.py)

**Purpose**: Central orchestrator and webhook handler

**Key Functions**:
- `voice_webhook()`: Initial call handler
- `process_webhook()`: Main processing pipeline
- `call_status_webhook()`: Cleanup handler
- `make_call()`: Outbound call initiator

**State Management**:
```python
conversation_history = {
    "CA123...": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
}
```

**Security**:
- Twilio request validation using `RequestValidator`
- Environment variable isolation
- HTTPS enforcement via ngrok

---

### 2. Twilio Integration

**Components Used**:
- **Voice API**: Call handling
- **TwiML**: XML responses for call control
- **Recording API**: Audio capture
- **REST API**: Outbound calls

**TwiML Flow**:
```xml
<!-- Initial greeting -->
<Response>
    <Say language="hi-IN">Namaste!</Say>
    <Record action="/process" maxLength="30" playBeep="true"/>
</Response>

<!-- Response playback -->
<Response>
    <Play>https://your-server.com/static/audio/file.wav</Play>
    <Record action="/process" maxLength="30"/>
</Response>
```

**Webhooks**:
- `/voice`: Call initiation (GET/POST)
- `/process`: Audio processing (POST)
- `/call-status`: Status updates (POST)
- `/recording-status`: Recording events (POST)

---

### 3. Sarvam AI STT

**API Endpoint**: `https://api.sarvam.ai/speech-to-text`

**Request Format**:
```python
files = {'file': ('audio.wav', audio_bytes, 'audio/wav')}
headers = {'api-subscription-key': API_KEY}
data = {
    'language_code': 'hi-IN',
    'model': 'saaras:v1'
}
```

**Response Format**:
```json
{
    "transcript": "नमस्ते, मैं कैसे मदद कर सकता हूं?",
    "language_code": "hi-IN",
    "duration": 2.5
}
```

**Error Handling**:
- Network timeout: 30s
- Retry: None (fallback to error message)
- Fallback: "Sorry, I didn't catch that"

---

### 4. Local LLM (Ollama)

**API Endpoint**: `http://localhost:11434/api/chat`

**Request Format**:
```json
{
    "model": "llama3.1:8b-instruct-q4_K_M",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant..."},
        {"role": "user", "content": "User message"},
        {"role": "assistant", "content": "Previous response"}
    ],
    "stream": false,
    "options": {
        "temperature": 0.7,
        "max_tokens": 150
    }
}
```

**Response Format**:
```json
{
    "message": {
        "role": "assistant",
        "content": "AI response text"
    },
    "done": true
}
```

**System Prompt**:
```
You are a helpful AI assistant for a voice call system.
Keep responses concise (2-3 sentences max) and natural for speech.
Speak in Hindi if the user speaks Hindi, otherwise use English.
Be friendly, helpful, and conversational.
```

**Conversation Context**:
- Full history maintained per CallSid
- Cleared on call end
- Max context: Limited by model's context window

---

### 5. Sarvam AI TTS

**API Endpoint**: `https://api.sarvam.ai/text-to-speech`

**Request Format**:
```json
{
    "inputs": ["Text to convert"],
    "target_language_code": "hi-IN",
    "speaker": "meera",
    "pitch": 0,
    "pace": 1.0,
    "loudness": 1.5,
    "speech_sample_rate": 8000,
    "enable_preprocessing": true,
    "model": "bulbul:v1"
}
```

**Response Format**:
```json
{
    "audios": ["base64_encoded_audio_data"]
}
```

**Audio Processing**:
1. Decode base64 audio
2. Save to `static/audio/{call_sid}_{uuid}.wav`
3. Generate public URL: `{BASE_URL}/static/audio/{filename}`
4. Return URL in TwiML

**Voice Configuration**:
- Speaker: `meera` (female, natural Hindi)
- Sample rate: 8000 Hz (telephony optimized)
- Format: WAV (PCM)

---

## 🔄 Data Flow

### Inbound Call Flow

```
┌──────────┐
│  Caller  │
└────┬─────┘
     │ 1. Dials Twilio number
     ▼
┌─────────────────┐
│  Twilio Cloud   │
└────┬────────────┘
     │ 2. POST /voice
     ▼
┌─────────────────────────────────────────┐
│  Flask Server                           │
│  ┌───────────────────────────────────┐  │
│  │ voice_webhook()                   │  │
│  │ - Initialize conversation history │  │
│  │ - Generate greeting TwiML         │  │
│  │ - Start recording                 │  │
│  └───────────────────────────────────┘  │
└────┬────────────────────────────────────┘
     │ 3. TwiML response
     ▼
┌─────────────────┐
│  Twilio Cloud   │
│  - Plays greeting│
│  - Records audio │
└────┬────────────┘
     │ 4. POST /process (with RecordingUrl)
     ▼
┌─────────────────────────────────────────┐
│  Flask Server                           │
│  ┌───────────────────────────────────┐  │
│  │ process_webhook()                 │  │
│  │                                   │  │
│  │ Step 1: Download audio            │  │
│  │   ↓                               │  │
│  │ Step 2: Sarvam STT                │  │
│  │   ↓                               │  │
│  │ Step 3: Update conversation       │  │
│  │   ↓                               │  │
│  │ Step 4: Call local LLM            │  │
│  │   ↓                               │  │
│  │ Step 5: Sarvam TTS                │  │
│  │   ↓                               │  │
│  │ Step 6: Save audio file           │  │
│  │   ↓                               │  │
│  │ Step 7: Generate TwiML            │  │
│  └───────────────────────────────────┘  │
└────┬────────────────────────────────────┘
     │ 5. TwiML with <Play> URL
     ▼
┌─────────────────┐
│  Twilio Cloud   │
│  - Plays response│
│  - Records next  │
└────┬────────────┘
     │ 6. Loop back to step 4
     ▼
   (Continues until call ends)
```

### Outbound Call Flow

```
┌─────────────────┐
│  Your App       │
└────┬────────────┘
     │ POST /make-call {"to_number": "+91..."}
     ▼
┌─────────────────────────────────────────┐
│  Flask Server                           │
│  ┌───────────────────────────────────┐  │
│  │ make_call()                       │  │
│  │ - Validate number                 │  │
│  │ - Call Twilio API                 │  │
│  └───────────────────────────────────┘  │
└────┬────────────────────────────────────┘
     │ Twilio REST API call
     ▼
┌─────────────────┐
│  Twilio Cloud   │
│  - Initiates call│
│  - Calls /voice  │
└────┬────────────┘
     │ (Same flow as inbound from here)
     ▼
```

---

## 💾 Storage & State

### Conversation History
```python
# In-memory dictionary
conversation_history = {
    "CA123abc...": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"}
    ]
}

# Lifecycle:
# - Created: On call start (/voice)
# - Updated: Each turn (/process)
# - Deleted: On call end (/call-status)
```

### Audio Files
```
static/audio/
├── CA123abc_a1b2c3d4.wav  # Call 1, turn 1
├── CA123abc_e5f6g7h8.wav  # Call 1, turn 2
└── CA456def_i9j0k1l2.wav  # Call 2, turn 1

# Lifecycle:
# - Created: After TTS generation
# - Served: Via /static/audio/<filename>
# - Deleted: On call end (/call-status)
```

---

## 🔒 Security Architecture

### 1. Twilio Request Validation
```python
@validate_twilio_request
def webhook():
    # Validates:
    # - X-Twilio-Signature header
    # - Request URL
    # - POST parameters
    # - Auth token match
    pass
```

### 2. Environment Variables
```
.env file (never committed)
├── TWILIO_ACCOUNT_SID
├── TWILIO_AUTH_TOKEN
├── SARVAM_API_KEY
└── Other sensitive config
```

### 3. HTTPS Enforcement
- ngrok provides automatic HTTPS
- Twilio requires HTTPS for webhooks
- All API calls use HTTPS

### 4. Input Validation
- Phone numbers validated
- Audio file size limits (50MB)
- Timeout limits on all external calls

---

## ⚡ Performance Considerations

### Latency Breakdown
```
Total response time: ~5-8 seconds

1. Audio download:     0.5s
2. Sarvam STT:        1-2s
3. Local LLM:         2-3s
4. Sarvam TTS:        1-2s
5. Audio save:        0.1s
6. TwiML generation:  0.1s
```

### Optimization Strategies
1. **Parallel processing**: Could parallelize STT + audio download
2. **Caching**: Cache common responses
3. **Streaming**: Stream LLM responses (requires async)
4. **Model optimization**: Use smaller/faster LLM models
5. **Audio compression**: Use lower sample rates

### Scalability
- **Current**: Single-threaded Flask (1 call at a time)
- **Production**: Use gunicorn with multiple workers
- **High scale**: Add Redis for conversation state, load balancer

---

## 🐛 Error Handling Strategy

### Error Categories

1. **STT Failure**
   - Cause: Sarvam API down, bad audio, no credits
   - Handling: Voice fallback message
   - Recovery: Continue conversation

2. **LLM Failure**
   - Cause: Ollama down, timeout, model error
   - Handling: Voice fallback message
   - Recovery: Continue conversation

3. **TTS Failure**
   - Cause: Sarvam API down, no credits
   - Handling: Twilio built-in TTS fallback
   - Recovery: Continue conversation

4. **Network Failure**
   - Cause: Internet down, API unreachable
   - Handling: Timeout + error message
   - Recovery: Retry or fallback

### Error Flow
```python
try:
    transcript = sarvam_stt(audio_url)
    if not transcript:
        # Fallback: Ask user to repeat
        return error_twiml("Please repeat")
except Exception as e:
    logger.error(f"STT error: {e}")
    return error_twiml("Technical difficulty")
```

---

## 📊 Monitoring & Logging

### Log Levels
```python
INFO:  Normal operations
ERROR: Failures requiring attention
DEBUG: Detailed debugging info
```

### Key Metrics to Monitor
1. **Call volume**: Active calls count
2. **Success rate**: Successful vs failed calls
3. **Latency**: Response time per component
4. **Error rate**: STT/LLM/TTS failures
5. **Audio files**: Storage usage

### Log Examples
```
2026-04-25 02:00:00 [INFO] Incoming call: CA123 from +91...
2026-04-25 02:00:05 [INFO] STT Success: नमस्ते
2026-04-25 02:00:08 [INFO] LLM Response: Hello! How can I help?
2026-04-25 02:00:10 [INFO] TTS audio saved: https://...
2026-04-25 02:05:00 [INFO] Call ended: CA123
```

---

## 🚀 Deployment Architecture

### Development (Current)
```
Laptop
├── Flask (localhost:5000)
├── Ollama (localhost:11434)
└── ngrok → Twilio
```

### Production (Recommended)
```
Cloud VM (AWS/GCP/DO)
├── nginx (reverse proxy, SSL)
├── gunicorn (Flask workers)
├── Ollama (local LLM)
├── systemd (process management)
└── Domain with SSL → Twilio
```

### Production Setup
```bash
# nginx config
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# systemd service
[Unit]
Description=Voice Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/voice-bot
ExecStart=/home/ubuntu/voice-bot/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🔄 Future Enhancements

### Short-term
1. Add conversation timeout (auto-end after silence)
2. Implement call recording storage
3. Add analytics dashboard
4. Support multiple languages dynamically

### Long-term
1. WebSocket for real-time streaming
2. Voice activity detection (VAD)
3. Emotion detection in voice
4. Multi-turn context compression
5. Redis for distributed state
6. Kubernetes deployment

---

## 📚 Technology Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | Flask 3.0 | Web framework |
| Telephony | Twilio | Call handling |
| STT | Sarvam AI | Speech recognition |
| LLM | Ollama (llama3.1) | Conversation AI |
| TTS | Sarvam AI | Voice synthesis |
| Tunneling | ngrok | Local→Public |
| Language | Python 3.8+ | Core language |
| State | In-memory dict | Conversation history |
| Storage | File system | Audio files |

---

## 🎯 Design Principles

1. **Simplicity**: Single file, minimal dependencies
2. **Reliability**: Error handling at every step
3. **Privacy**: Local LLM, no cloud AI
4. **Cost-effective**: Only pay for Twilio + Sarvam
5. **Maintainability**: Clear code, good logging
6. **Security**: Request validation, HTTPS
7. **Scalability**: Easy to add workers/Redis

---

This architecture provides a solid foundation for a production voice AI system while remaining simple enough to understand and modify.
