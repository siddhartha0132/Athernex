"""
Test language detection functionality
"""

from language_detector import detect_language, get_language_name, get_tts_language_code

# Test cases
test_cases = [
    ("Hello, how are you?", "en", "English"),
    ("नमस्ते, आप कैसे हैं?", "hi", "Hindi"),
    ("I want to order pizza", "en", "English"),
    ("मुझे पिज़्ज़ा ऑर्डर करना है", "hi", "Hindi"),
    ("What is your name?", "en", "English"),
    ("आपका नाम क्या है?", "hi", "Hindi"),
    ("Good morning", "en", "English"),
    ("शुभ प्रभात", "hi", "Hindi"),
    ("Thank you very much", "en", "English"),
    ("बहुत धन्यवाद", "hi", "Hindi"),
]

print("=" * 70)
print("Language Detection Test")
print("=" * 70)

passed = 0
failed = 0

for text, expected_code, expected_name in test_cases:
    detected = detect_language(text)
    lang_name = get_language_name(detected)
    tts_code = get_tts_language_code(detected)
    
    status = "✅ PASS" if detected == expected_code else "❌ FAIL"
    
    if detected == expected_code:
        passed += 1
    else:
        failed += 1
    
    print(f"\n{status}")
    print(f"Text: {text}")
    print(f"Expected: {expected_name} ({expected_code})")
    print(f"Detected: {lang_name} ({detected})")
    print(f"TTS Code: {tts_code}")

print("\n" + "=" * 70)
print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 70)

if failed == 0:
    print("🎉 All tests passed! Language detection is working correctly.")
else:
    print(f"⚠️  {failed} test(s) failed. Check the detection logic.")
