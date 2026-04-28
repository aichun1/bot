"""
Google OAuth token.json ni olish uchun bu scriptni LOCAL kompyuterda ishlatng.
1. Google Cloud Console → APIs & Services → Credentials
2. OAuth 2.0 Client ID → Desktop app → JSON yuklab olish
3. Yuklab olingan faylni credentials.json deb saqlang
4. Bu scriptni ishlatng

Ishlatish:
  pip install google-auth-oauthlib google-api-python-client
  python setup_google.py
"""
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive",
]

print("=" * 50)
print("  SuperBot — Google OAuth Setup")
print("=" * 50)
print()
print("credentials.json faylini joriy papkaga joylashtiring.")
input("Tayyor bo'lsa Enter bosing...")

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)

with open("token.json", "w") as f:
    f.write(creds.to_json())

print()
print("✅ token.json saqlandi!")
print("Bu faylni Railway ga environment variable sifatida yuboring:")
print()
with open("token.json") as f:
    data = json.load(f)
    print("GOOGLE_TOKEN_JSON ning qiymati = token.json faylining BUTUN tarkibi")
print()
print("Yoki token.json faylini loyiha papkasiga ko'chiring (git ignore qilingan).")
