"""
Bu scriptni LOCAL kompyuterda bir marta ishlatib SESSION_STRING oling.
Keyin uni .env fayliga joylashtiring.

Ishlatish:
  pip install telethon python-dotenv
  python get_session.py
"""
import asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("=" * 50)
print("  SuperBot — Session String Generator")
print("=" * 50)
print()

api_id = int(input("API_ID (my.telegram.org dan): ").strip())
api_hash = input("API_HASH: ").strip()
phone = input("Telefon raqam (+998...): ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    client.start(phone=phone)
    session_string = client.session.save()

print()
print("=" * 50)
print("✅ SESSION_STRING:")
print()
print(session_string)
print()
print("=" * 50)
print("Bu qatorni .env faylida SESSION_STRING= ga paste qiling!")
