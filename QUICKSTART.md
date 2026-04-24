# 🚀 Quick Start Guide

Get your AI Voice Call System running in 5 minutes.

---

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] Ollama installed with llama3.1 model
- [ ] ngrok installed and authenticated
- [ ] Twilio account with phone number
- [ ] Sarvam AI API key

---

## 5-Minute Setup

### 1. Install Dependencies (1 min)

```bash
cd voice-bot
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment (1 min)

Create `.env` file:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
SARVAM_API_KEY=your_sarvam_key
LOCAL_LLM_URL=http://localhost:11434/api/chat
LOCAL_LLM_MODEL=llama3.1:8b-instruct-q4_K_M
BASE_URL=http://localhost:5000
LANGUAGE_CODE=hi-IN
```

### 3. Start Services (2 min)

**Terminal 1 - Ollama**:
```bash
ollama serve
```

**Terminal 2 - Flask**:
```bash
python app.py
```

**Terminal 3 - ngrok**:
```bash
ngrok http 5000
```

Copy the ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`)

### 4. Update Configuration (30 sec)

Edit `.env`:
```env
BASE_URL=https://abc123.ngrok.io
```

Restart Flask (Ctrl+C and `python app.py`)

### 5. Configure Twilio (30 sec)

1. Go to https://console.twilio.com/
2. Phone Numbers → Your Number
3. Voice Configuration:
   - A CALL COMES IN: `https://abc123.ngrok.io/voice` (POST)
   - CALL STATUS CHANGES: `https://abc123.ngrok.io/call-status` (POST)
4. Save

---

## Test Your System

### Test 1: Health Check
```bash
curl http://localhost:5000/health
```

Expected: `{"status": "healthy"}`

### Test 2: Make a Call

Call your Twilio number from your phone. You should hear:
> "Namaste! Main aapki AI assistant hoon. Aap mujhse kuch bhi pooch sakte hain."

Speak in Hindi or English, and the AI will respond!

---

## Common Issues

### "Missing required environment variables"
→ Check all variables in `.env` are filled

### "Twilio can't reach my server"
→ Verify ngrok URL matches BASE_URL in `.env`

### "STT fails"
→ Check Sarvam API key and credits

### "LLM fails"
→ Verify Ollama is running: `curl http://localhost:11434/api/tags`

---

## What's Happening?

```
You call → Twilio → Flask → Sarvam STT → Language Detection
                                              ↓
                                         Local LLM
                                              ↓
                                         Sarvam TTS
                                              ↓
                                    Audio plays back to you
```

---

## Next Steps

- Read [COMPLETE_SYSTEM_ANALYSIS.md](COMPLETE_SYSTEM_ANALYSIS.md) for deep dive
- Read [README.md](README.md) for full documentation
- Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Test language detection with Hindi and English
- Try the web interface: [test_web_interface.html](test_web_interface.html)

---

## Support

Check logs in your Flask terminal for detailed information about what's happening during calls.

**You're all set! 🎉**
