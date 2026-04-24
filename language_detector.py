"""
Simple language detector for Hindi/English text
Uses character-based detection
"""

import re

def detect_language(text: str) -> str:
    """
    Detect if text is Hindi or English
    
    Args:
        text: Input text
    
    Returns:
        'hi' for Hindi, 'en' for English
    """
    if not text:
        return 'en'
    
    # Count Devanagari characters (Hindi)
    devanagari_chars = len(re.findall(r'[\u0900-\u097F]', text))
    
    # Count English characters
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    
    # If more than 30% Devanagari, it's Hindi
    total_chars = len(text.replace(' ', ''))
    if total_chars > 0:
        hindi_ratio = devanagari_chars / total_chars
        if hindi_ratio > 0.3:
            return 'hi'
    
    # If more English than Hindi, it's English
    if english_chars > devanagari_chars:
        return 'en'
    
    # Default to Hindi (since we're targeting Indian users)
    return 'hi' if devanagari_chars > 0 else 'en'


def get_language_name(code: str) -> str:
    """Get full language name from code"""
    return {
        'hi': 'Hindi',
        'en': 'English',
        'hi-IN': 'Hindi',
        'en-IN': 'English'
    }.get(code, 'English')


def get_tts_language_code(detected_lang: str) -> str:
    """Convert detected language to TTS language code"""
    if detected_lang == 'hi':
        return 'hi-IN'
    return 'en-IN'
