from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

print("=" * 60)
print("Twilio Number Configuration Check")
print("=" * 60)

numbers = client.incoming_phone_numbers.list()

for n in numbers:
    print(f"\nNumber: {n.phone_number}")
    print(f"Friendly Name: {n.friendly_name}")
    print(f"Voice Enabled: {n.capabilities['voice']}")
    print(f"SMS Enabled: {n.capabilities['sms']}")
    print(f"Voice URL: {n.voice_url or 'Not configured'}")
    print(f"Voice Method: {n.voice_method}")
    print(f"Status Callback: {n.status_callback or 'Not configured'}")

print("\n" + "=" * 60)
print("Account Info")
print("=" * 60)

account = client.api.accounts(os.getenv('TWILIO_ACCOUNT_SID')).fetch()
print(f"Account Type: {account.type}")
print(f"Account Status: {account.status}")

if account.type == 'Trial':
    print("\n⚠️  This is a TRIAL account!")
    print("You can only call VERIFIED phone numbers.")
    print("Verify your phone at: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
