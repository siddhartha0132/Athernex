from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

# Enter YOUR phone number here (the one you want to receive the call on)
YOUR_PHONE_NUMBER = input("Enter your phone number (with country code, e.g., +919876543210): ")

print(f"\nMaking test call to {YOUR_PHONE_NUMBER}...")

try:
    call = client.calls.create(
        to=YOUR_PHONE_NUMBER,
        from_=os.getenv('TWILIO_PHONE_NUMBER'),
        url=f"{os.getenv('BASE_URL')}/voice",
        status_callback=f"{os.getenv('BASE_URL')}/call-status",
        status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
        status_callback_method='POST'
    )
    
    print(f"✅ Call initiated!")
    print(f"Call SID: {call.sid}")
    print(f"Status: {call.status}")
    print(f"\nYour phone should ring in a few seconds...")
    
except Exception as e:
    print(f"❌ Error: {e}")
    if "not a verified" in str(e).lower():
        print("\n⚠️  Your phone number is not verified!")
        print("Verify it at: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
