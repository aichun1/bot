# 🤖 SuperBot — Shaxsiy Telegram Super Bot

Shaxsiy Telegram bot — userbot orqali **cheksiz imkoniyatlar**.

---

## ✨ Imkoniyatlar

| Soha | Nima qiladi |
|------|-------------|
| 📨 Xabarlar | Yuborish, forward, o'chirish, pin, broadcast |
| 👥 Guruhlar | A'zolar, tarix, qidirish, mute |
| ⏰ Rejalashtirish | Belgilangan vaqtda xabar yuborish |
| 🤖 AI | Telegram AI botlari orqali javob |
| 🎙️ Ovoz | Audio → matnga aylantirish (Whisper) |
| 📅 Calendar | Google Calendar boshqaruvi |
| 📧 Gmail | Emaillarni ko'rish va yuborish |
| 💾 Drive | Google Drive qidirish va yuklash |
| 👁️ Monitor | Kanal/guruhlarda kalit so'z kuzatish |
| 🔄 Autoreply | Avtomatik javob |
| 🚫 Blacklist | Taqiqlangan chatlar ro'yxati |

---

## 🚀 O'rnatish

### 1. Talablar

- Python 3.11+
- Telegram Bot token ([@BotFather](https://t.me/BotFather))
- Telegram API ID/Hash ([my.telegram.org](https://my.telegram.org))
- GitHub akkaunt
- [Railway](https://railway.app) akkaunt

---

### 2. Loyihani klonlash

```bash
git clone https://github.com/SIZNING_USERNAME/superbot.git
cd superbot
pip install -r requirements.txt
```

---

### 3. SESSION_STRING olish (bir marta, local)

```bash
python get_session.py
```

Chiqgan `SESSION_STRING` ni saqlang.

---

### 4. Google API sozlash (ixtiyoriy)

1. [Google Cloud Console](https://console.cloud.google.com) → yangi loyiha
2. APIs & Services → Enable:
   - Google Calendar API
   - Gmail API  
   - Google Drive API
3. Credentials → OAuth 2.0 Client ID → Desktop → JSON yuklab olish
4. `credentials.json` deb saqlang
5. Ishlatish:
```bash
python setup_google.py
```
Bu `token.json` yaratadi.

---

### 5. .env faylini sozlash

```bash
cp .env.example .env
```

`.env` faylini to'ldiring:

```env
BOT_TOKEN=...
OWNER_ID=...
BOT_PASSWORD=...
API_ID=...
API_HASH=...
SESSION_STRING=...
```

---

### 6. Lokal sinash

```bash
python main.py
```

---

### 7. Railway ga deploy qilish

```bash
# GitHub ga push
git add .
git commit -m "Initial commit"
git push origin main
```

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Reponi tanlang
3. Variables bo'limiga `.env` dagi barcha qiymatlarni kiriting
4. Deploy!

---

## 📋 Buyruqlar

```
/help       — Barcha buyruqlar
/send       — Xabar yuborish
/forward    — Forward
/delete     — O'chirish
/pin        — Pin qilish
/broadcast  — Ko'p guruhga yuborish
/members    — A'zolar
/history    — Tarix
/search     — Qidirish
/mute       — Jim qilish
/schedule   — Vaqtli xabar
/ai         — AI savol
/audio      — Ovoz → matn
/cal        — Calendar
/gmail      — Email
/drive      — Drive
/monitor    — Kuzatish
/autoreply  — Avtomatik javob
/bl         — Qora ro'yxat
/status     — Holat
/digest     — Hisobot
```

---

## 🔐 Xavfsizlik

- Parolni `.env` da saqlang, hech kimga bermang
- `SESSION_STRING` — bu sizning akkauntingizga to'liq kirish. **Maxfiy saqlang!**
- `.gitignore` da `.env`, `token.json`, `*.session` qo'shilgan

---

## 🛠️ Texnologiyalar

- **[Telethon](https://github.com/LonamiWebs/Telethon)** — Userbot
- **[Aiogram 3](https://docs.aiogram.dev)** — Bot framework
- **[APScheduler](https://apscheduler.readthedocs.io)** — Rejalashtirilgan vazifalar
- **[aiosqlite](https://aiosqlite.omnilib.dev)** — Ma'lumotlar bazasi
- **[Railway](https://railway.app)** — Hosting
