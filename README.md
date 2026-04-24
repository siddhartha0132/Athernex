# 🤖 AI Voice Call System
## Twilio + Sarvam AI + Local LLM (Ollama)

Production-ready voice call system with Hindi speech recognition, local AI intelligence, and natural voice responses.

---

## 📋 Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

---

## ✨ Features

- ✅ **Inbound Calls**: Receive calls on your Twilio number
- ✅ **Outbound Calls**: Programmatically initiate calls
- ✅ **Hindi Speech Recognition**: Sarvam AI STT with hi-IN support
- ✅ **Local LLM**: Privacy-first AI using Ollama (no cloud AI costs)
- ✅ **Natural Voice**: Sarvam AI TTS with Indian voice (Meera)
- ✅ **Conversation Memory**: Full context maintained across turns
- ✅ **Error Handling**: Graceful fallbacks at every step
- ✅ **Auto Cleanup**: Audio files deleted after call ends
- ✅ **Security**: Twilio request validation on all webhooks

---

## 🏗️ Architecture

```
┌─────────────┐
│   Caller    │
└──────┬──────┘
       │ 1. Dials Twilio number
       ▼
┌─────────────────────────────────────────────────────────┐
│                    TWILIO CLOUD                         │
│  • Receives call                                        │
│  • Records audio                                        │
│  • Sends webhooks to your server                       │
└──────────────────────┬──────────────────────────────────┘
                       │ 2. Webhook: /voice
                       ▼
┌─────────────────────────────────────────────────────────┐
│              YOUR SERVER (Flask + ngrok)                │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  /voice → Greet & Start Recording               │  │
│  └─────────────────────────────────────────────────┘  │
│                       │                                 │
│                       │ 3. User speaks                  │
│                       ▼                                 │
│  ┌─────────────────────────────────────────────────┐  │
│  │  /process → Download audio from Twilio          │  │
│  │           ↓                                      │  │
│  │           Send to Sarvam AI STT                 │  │
│  │           ↓                                      │  │
│  │           Get transcript                        │  │
│  │           ↓                                      │  │
│  │           Send to Local LLM (Ollama)            │  │
│  │           ↓                                      │  │
│  │           Get AI response                       │  │
│  │           ↓                                      │  │
│  │           Send to Sarvam AI TTS                 │  │
│  │           ↓                                      │  │
│  │           Save audio file                       │  │
│  │           ↓                                      │  │
│  │           Return TwiML with <Play> URL          │  │
│  └─────────────────────────────────────────────────┘  │
│                       │                                 │
│                       │ 4. Play response                │
│                       ▼                                 │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Loop back to recording next input              │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  /call-status → Cleanup when call ends          │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Prerequisites

### 1. **Twilio Account**
- Sign up at https://www.twilio.com
- Get a phone number with voice capabilities
- Note your Account SID and Auth Token

### 2. **Sarvam AI Account**
- Sign up at https://www.sarvam.ai
- Get your API key from the dashboard
- Ensure you have STT and TTS access

### 3. **Local LLM (Ollama)**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (recommended: llama3.1)
ollama pull llama3.1:8b-instruct-q4_K_M

# Verify it's running
curl http://localhost:11434/api/tags
```

### 4. **Python 3.8+**
```bash
python --version  # Should be 3.8 or higher
```

### 5. **ngrok**
```bash
# Install ngrok
# Windows: Download from https://ngrok.com/download
# Mac: brew install ngrok
# Linux: snap install ngrok

# Authenticate (get token from https://dashboard.ngrok.com)
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

---

## 🚀 Installation

### Step 1: Clone/Download the Project
```bash
cd voice-bot
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Create .env File
```bash
# Copy the example
cp .env.example .env

# Edit .env with your credentials
# Windows: notepad .env
# Mac/Linux: nano .env
```

Fill in your actual credentials:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
SARVAM_API_KEY=your_sarvam_api_key_here
LOCAL_LLM_URL=http://localhost:11434/api/chat
LOCAL_LLM_MODEL=llama3.1:8b-instruct-q4_K_M
BASE_URL=https://your-ngrok-url.ngrok.io
LANGUAGE_CODE=hi-IN
```

---

## ⚙️ Configuration

### Environment Variables Explained

| Variable | Description | Example |
|----------|-------------|---------|
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID | `ACxxxxxxxx...` |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token | `your_token` |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number | `+1234567890` |
| `SARVAM_API_KEY` | Sarvam AI API key | `your_key` |
| `LOCAL_LLM_URL` | Ollama API endpoint | `http://localhost:11434/api/chat` |
| `LOCAL_LLM_MODEL` | Ollama model name | `llama3.1:8b-instruct-q4_K_M` |
| `BASE_URL` | Your public ngrok URL | `https://abc123.ngrok.io` |
| `LANGUAGE_CODE` | Speech language code | `hi-IN` (Hindi), `en-IN` (English) |

---

## 🏃 Running the System

### Step 1: Start Ollama (if not running)
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve
```

### Step 2: Start Flask Server
```bash
# Make sure you're in the voice-bot directory with venv activated
python app.py
```

You should see:
```
============================================================
🚀 AI Voice Call System Starting
============================================================
📞 Twilio Phone: +1234567890
🌐 Base URL: http://localhost:5000
🗣️  Language: hi-IN
🤖 LLM Model: llama3.1:8b-instruct-q4_K_M
📁 Audio Directory: /path/to/voice-bot/static/audio
============================================================
 * Running on http://0.0.0.0:5000
```

### Step 3: Start ngrok (in a new terminal)
```bash
ngrok http 5000
```

You'll see output like:
```
Forwarding  https://abc123def456.ngrok.io -> http://localhost:5000
```

**Copy the https URL** (e.g., `https://abc123def456.ngrok.io`)

### Step 4: Update .env with ngrok URL
```bash
# Edit .env
BASE_URL=https://abc123def456.ngrok.io
```

**Restart Flask server** (Ctrl+C and run `python app.py` again)

### Step 5: Configure Twilio Webhooks

1. Go to https://console.twilio.com/
2. Navigate to **Phone Numbers** → **Manage** → **Active Numbers**
3. Click on your phone number
4. Scroll to **Voice Configuration**
5. Set:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://your-ngrok-url.ngrok.io/voice`
   - **HTTP**: POST
6. Scroll to **Call Status Changes**
7. Set:
   - **URL**: `https://your-ngrok-url.ngrok.io/call-status`
   - **HTTP**: POST
8. Click **Save**

---

## 🧪 Testing

### Test 1: Inbound Call
1. Call your Twilio phone number from your mobile
2. You should hear: "Namaste! Main aapki AI assistant hoon..."
3. Speak in Hindi or English
4. The AI should respond naturally
5. Continue the conversation

### Test 2: Outbound Call
```bash
curl -X POST http://localhost:5000/make-call \
  -H "Content-Type: application/json" \
  -d '{"to_number": "+919876543210"}'
```

### Test 3: Health Check
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-25T02:00:00",
  "active_conversations": 0
}
```

---

## 🐛 Troubleshooting

### Problem: "Missing required environment variables"
**Solution**: Check your `.env` file has all required variables filled in.

### Problem: "Twilio can't reach my server"
**Solutions**:
1. Verify ngrok is running: `curl https://your-ngrok-url.ngrok.io/health`
2. Check Flask is running on port 5000
3. Ensure BASE_URL in .env matches your ngrok URL
4. Restart Flask after changing .env

### Problem: "STT fails - 'Sorry, I didn't catch that'"
**Solutions**:
1. Check Sarvam AI API key is correct
2. Verify you have STT credits in Sarvam dashboard
3. Check logs for API error messages
4. Test Sarvam API directly:
```bash
curl -X POST https://api.sarvam.ai/speech-to-text \
  -H "api-subscription-key: YOUR_KEY" \
  -F "file=@test.wav" \
  -F "language_code=hi-IN"
```

### Problem: "LLM fails - 'I'm having trouble thinking'"
**Solutions**:
1. Check Ollama is running: `curl http://localhost:11434/api/tags`
2. Verify model is pulled: `ollama list`
3. Test LLM directly:
```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.1:8b-instruct-q4_K_M",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": false
}'
```

### Problem: "TTS fails - using fallback voice"
**Solutions**:
1. Check Sarvam AI TTS credits
2. Verify API key has TTS access
3. Check logs for specific error
4. Test TTS API:
```bash
curl -X POST https://api.sarvam.ai/text-to-speech \
  -H "api-subscription-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": ["Namaste"],
    "target_language_code": "hi-IN",
    "speaker": "meera",
    "model": "bulbul:v1"
  }'
```

### Problem: "Audio files not playing"
**Solutions**:
1. Check `static/audio/` folder exists
2. Verify BASE_URL is correct (must be https ngrok URL)
3. Check file permissions
4. Look for audio files: `ls static/audio/`

### Problem: "Call ends immediately"
**Solutions**:
1. Check Twilio webhook URLs are correct
2. Verify ngrok is still running (it times out after 2 hours on free plan)
3. Check Flask logs for errors
4. Test webhook manually:
```bash
curl -X POST https://your-ngrok-url.ngrok.io/voice \
  -d "CallSid=TEST123" \
  -d "From=+1234567890"
```

### Problem: "Conversation doesn't remember context"
**Solution**: This is normal - conversation history is stored in memory and cleared when:
- Call ends
- Server restarts
- Check logs to see if history is being maintained

### Problem: "ngrok URL keeps changing"
**Solutions**:
1. Get a static ngrok domain (paid plan)
2. Or update Twilio webhooks each time ngrok restarts
3. Use a script to auto-update:
```bash
# Get current ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*')
echo "New ngrok URL: $NGROK_URL"
# Update .env and restart Flask
```

---

## 📚 API Reference

### Webhooks (Called by Twilio)

#### POST /voice
Initial webhook when call is received.
- **Called by**: Twilio
- **Returns**: TwiML with greeting and recording instructions

#### POST /process
Process recorded audio and generate response.
- **Called by**: Twilio after recording
- **Parameters**: 
  - `CallSid`: Unique call identifier
  - `RecordingUrl`: URL of recorded audio
- **Returns**: TwiML with AI response audio

#### POST /call-status
Handle call status updates.
- **Called by**: Twilio on status changes
- **Parameters**:
  - `CallSid`: Unique call identifier
  - `CallStatus`: completed, failed, busy, etc.
- **Action**: Cleans up conversation history and audio files

### REST API (Your Application)

#### POST /make-call
Initiate an outbound call.
```bash
curl -X POST http://localhost:5000/make-call \
  -H "Content-Type: application/json" \
  -d '{"to_number": "+919876543210"}'
```

**Response**:
```json
{
  "success": true,
  "call_sid": "CAxxxxxxxx",
  "to": "+919876543210",
  "status": "queued"
}
```

#### GET /health
Health check endpoint.
```bash
curl http://localhost:5000/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-25T02:00:00",
  "active_conversations": 2
}
```

#### GET /
API information.
```bash
curl http://localhost:5000/
```

---

## 🔒 Security Notes

1. **Never commit .env file** - it contains sensitive credentials
2. **Twilio request validation** - all webhooks validate Twilio signatures
3. **HTTPS required** - ngrok provides this automatically
4. **Rate limiting** - consider adding rate limits in production
5. **Audio cleanup** - files are automatically deleted after calls

---

## 📊 Monitoring

### View Logs
```bash
# Flask logs show all activity
python app.py

# Look for:
# - "Incoming call: CAxxxx from +1234567890"
# - "STT Success: transcript text"
# - "LLM Response: response text"
# - "TTS audio saved: url"
```

### Check Active Calls
```bash
curl http://localhost:5000/
# Shows "active_calls" count
```

### Monitor Audio Files
```bash
# Windows
dir static\audio

# Mac/Linux
ls -lh static/audio/
```

---

## 🚀 Production Deployment

For production, replace ngrok with:
1. **Cloud VM** (AWS EC2, Google Cloud, DigitalOcean)
2. **Domain name** with SSL certificate
3. **Reverse proxy** (nginx)
4. **Process manager** (systemd, supervisor)
5. **Monitoring** (Prometheus, Grafana)

Example production setup:
```bash
# Install on Ubuntu server
sudo apt update
sudo apt install python3-pip nginx certbot

# Clone your code
git clone your-repo
cd voice-bot

# Install dependencies
pip3 install -r requirements.txt

# Setup nginx reverse proxy
sudo nano /etc/nginx/sites-available/voice-bot

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# Run with gunicorn
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 📝 License

This project is provided as-is for educational and commercial use.

---

## 🤝 Support

For issues:
1. Check the troubleshooting section
2. Review Flask logs
3. Test each component individually (STT, LLM, TTS)
4. Verify all credentials are correct

---

## 🎉 Success Checklist

- [ ] Ollama running with model pulled
- [ ] Flask server running on port 5000
- [ ] ngrok running and forwarding to localhost:5000
- [ ] .env file filled with all credentials
- [ ] BASE_URL in .env matches ngrok URL
- [ ] Twilio webhooks configured with ngrok URL
- [ ] Test call successful
- [ ] Audio files being generated
- [ ] Conversation context maintained
- [ ] Call cleanup working

**If all checked, you're ready to go! 🚀**
