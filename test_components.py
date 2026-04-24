"""
Component Testing Script
Test each component individually before running the full system
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_ollama():
    """Test local LLM connection"""
    print("\n🤖 Testing Ollama LLM...")
    try:
        url = os.getenv('LOCAL_LLM_URL', 'http://localhost:11434/api/chat')
        model = os.getenv('LOCAL_LLM_MODEL', 'llama3.1:8b-instruct-q4_K_M')
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Say hello in one word"}],
            "stream": False
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        llm_response = result.get('message', {}).get('content', '')
        
        print(f"✅ Ollama working! Response: {llm_response}")
        return True
    except Exception as e:
        print(f"❌ Ollama failed: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return False


def test_sarvam_tts():
    """Test Sarvam AI TTS"""
    print("\n🔊 Testing Sarvam AI TTS...")
    try:
        api_key = os.getenv('SARVAM_API_KEY')
        if not api_key:
            print("❌ SARVAM_API_KEY not set in .env")
            return False
        
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            'api-subscription-key': api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': ['Namaste'],
            'target_language_code': 'hi-IN',
            'speaker': 'meera',
            'model': 'bulbul:v1'
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        
        result = response.json()
        audio = result.get('audios', [None])[0]
        
        if audio:
            print(f"✅ Sarvam TTS working! Audio length: {len(audio)} chars")
            return True
        else:
            print("❌ No audio returned from Sarvam TTS")
            return False
    except Exception as e:
        print(f"❌ Sarvam TTS failed: {e}")
        print("   Check your SARVAM_API_KEY and credits")
        return False


def test_twilio():
    """Test Twilio credentials"""
    print("\n📞 Testing Twilio credentials...")
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            print("❌ Twilio credentials not set in .env")
            return False
        
        client = Client(account_sid, auth_token)
        
        # Try to fetch account info
        account = client.api.accounts(account_sid).fetch()
        
        print(f"✅ Twilio working! Account: {account.friendly_name}")
        return True
    except Exception as e:
        print(f"❌ Twilio failed: {e}")
        print("   Check your TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
        return False


def test_flask_server():
    """Test if Flask server is running"""
    print("\n🌐 Testing Flask server...")
    try:
        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
        
        # Try localhost first
        response = requests.get('http://localhost:5000/health', timeout=5)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Flask server running! Status: {result.get('status')}")
        return True
    except Exception as e:
        print(f"❌ Flask server not reachable: {e}")
        print("   Start the server: python app.py")
        return False


def test_ngrok():
    """Test if ngrok is running and accessible"""
    print("\n🌉 Testing ngrok tunnel...")
    try:
        base_url = os.getenv('BASE_URL', '')
        
        if 'localhost' in base_url or '127.0.0.1' in base_url:
            print("⚠️  BASE_URL is localhost - ngrok not configured")
            print("   Start ngrok: ngrok http 5000")
            print("   Update BASE_URL in .env with ngrok URL")
            return False
        
        response = requests.get(f"{base_url}/health", timeout=5)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ ngrok tunnel working! URL: {base_url}")
        return True
    except Exception as e:
        print(f"❌ ngrok tunnel not reachable: {e}")
        print("   1. Start ngrok: ngrok http 5000")
        print("   2. Update BASE_URL in .env")
        print("   3. Restart Flask server")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Component Testing")
    print("=" * 60)
    
    results = {
        "Ollama LLM": test_ollama(),
        "Sarvam TTS": test_sarvam_tts(),
        "Twilio": test_twilio(),
        "Flask Server": test_flask_server(),
        "ngrok Tunnel": test_ngrok()
    }
    
    print("\n" + "=" * 60)
    print("📊 Test Results")
    print("=" * 60)
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component:20} {status}")
    
    all_passed = all(results.values())
    
    print("=" * 60)
    if all_passed:
        print("🎉 All tests passed! System ready to use.")
        print("\n📞 Next steps:")
        print("   1. Configure Twilio webhooks")
        print("   2. Call your Twilio number")
        print("   3. Test the conversation!")
    else:
        print("⚠️  Some tests failed. Fix the issues above.")
        print("\n💡 Quick fixes:")
        print("   - Ollama: ollama serve")
        print("   - Flask: python app.py")
        print("   - ngrok: ngrok http 5000")
        print("   - Credentials: Check .env file")
    print("=" * 60)


if __name__ == '__main__':
    main()
