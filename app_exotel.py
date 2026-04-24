"""
Production-Ready AI Voice Call System - EXOTEL VERSION
Exotel + Sarvam AI (STT/TTS) + Local LLM (Ollama)

Architecture:
- Exotel handles telephony and call routing (Indian platform)
- Sarvam AI provides Hindi/English STT and TTS
- Local Ollama LLM for conversation intelligence
- Flask serves webhooks and audio files
- Conversation history maintained per CallSid
- Language detection for Hindi/English
"""

import os
import logging
import requests
import uuid
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlencode

from flask import Flask, request, send_from_directory, jsonify, Response
from dotenv import load_dotenv

# Import language detector
from language_detector import detect_language, get_language_name, get_tts_language_code

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Exotel Configuration
EXOTEL_SID = os.getenv('EXOTEL_SID')
EXOTEL_API_KEY = os.getenv('EXOTEL_API_KEY')
