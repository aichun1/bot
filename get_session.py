"""
SESSION_STRING olish uchun lokal kompyuterda bir marta ishlatiladi.

Ishlatish:
  pip install telethon
  python get_session.py
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("=" * 50)
print("  SuperBot — Session String Generator")
print("=" * 50)
print()

api_id   = int(input("API_ID   : ").strip())
api_hash = input("API_HASH : ").strip()
phone    = input("Telefon  (+998...): ").strip()

# + bo'lmasa qo'shamiz
if not phone.startswith("+"):
    phone = "+" + phone

print(f"\n📱 {phone} ga SMS kod yuborilmoqda...\n")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    # phone=lambda sifatida beramiz — Telethon qayta so'ramaydi
    client.start(phone=lambda: phone)
    session_string = client.session.save()

print()
print("=" * 60)
print("✅  SESSION_STRING tayyor!\n")
print(session_string)
print()
print("=" * 60)
print("↑ Yuqoridagi uzun satrni to'liq ko'chirib Railway da")
print("  SESSION_STRING  o'zgaruvchisiga joylashtiring.")
