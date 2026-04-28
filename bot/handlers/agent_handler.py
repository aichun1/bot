import json
import logging
from aiogram import Router, F
from aiogram.types import Message
from google_apis.gemini_api import gemini
from userbot.client import UserBotClient

log = logging.getLogger("agent")
router = Router()

AGENT_SYSTEM_PROMPT = """Siz SuperBot avtonom agentisiz (OpenClaw arxitekturasi asosida ishlaysiz).
Foydalanuvchi sizga erkin tilda buyruq beradi. Siz qadam-baqadam fikrlab, kerakli vositadan (tool) foydalanib, natija qaytarishingiz kerak.

Mavjud vositalar (Tools):
1. send_message
   - Maqsad: Biror kishiga yoki guruhga xabar yuborish.
   - Parametrlar: "peer" (ism yoki username), "text" (xabar matni)
   
2. ask_telegram_bot
   - Maqsad: Guruhdagi boshqa bepul AI botlardan yordam so'rash yoki murakkab muammoni yechtirish (masalan, qanday kod yozish kerakligini bilmasangiz).
   - Parametrlar: "bot_username" (masalan, @ChatGPT_bot yoki boshqa AI bot), "question" (so'rov matni)

3. execute_telethon
   - Maqsad: Yuqoridagilar bilan qilib bo'lmaydigan qolgan HAR QANDAY ishni qilish (yangi kanal ochish, profil rasmini o'zgartirish, ovozli xabar jo'natish, guruh a'zolarini o'chirish).
   - Parametrlar: "code" (Telethon uchun asinxron Python kodi. `client` o'zgaruvchisi tayyor holda ulanadi. Misol: `await client(functions.channels.CreateChannelRequest(title='test', about='', broadcast=True))`)

Agar vazifa murakkab bo'lsa va Telethon kodi qanday yozilishini bilmasangiz, avval `ask_telegram_bot` orqali boshqa botdan kodni qanday yozishni so'rang, keyingi bosqichda olingan javob asosida uni `execute_telethon` orqali sining.

Siz FAQAT quyidagi JSON formatida javob qaytarishingiz kerak:
{
  "thought": "Bu yerda vazifani qanday bajarish haqida o'ylang. Qaysi tool kerak?",
  "tool": "send_message" yoki "ask_telegram_bot" yoki "execute_telethon" yoki "done",
  "tool_args": {
     // tanlangan tool uchun kerakli parametrlar (agar done bo'lsa bo'sh)
  },
  "answer": "Foydalanuvchiga nima deyishingiz (agar tool 'done' bo'lsa, yakuniy javobingizni shu yerga yozing)"
}
Agar vazifa to'liq yakunlangan bo'lsa, "tool" ga "done" yozing va "answer" da natijani foydalanuvchiga bering.
"""

@router.message(F.text & ~F.text.startswith("/"))
async def handle_agent_text(message: Message, userbot: UserBotClient):
    prompt = message.text
    wait = await message.answer("🤖 Agent o'ylamoqda...")
    
    max_steps = 6
    conversation_history = f"Foydalanuvchi buyrug'i: {prompt}\n\nQadamlar tarixi:\n"
    
    for step in range(max_steps):
        try:
            # Gemini-dan navbatdagi qadamni so'raymiz
            response_text = await gemini.agent_ask(conversation_history, AGENT_SYSTEM_PROMPT)
            
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                log.error(f"Agent JSON parse error: {response_text}")
                await wait.edit_text(f"❌ Agent noto'g'ri format qaytardi (JSON kutilgan edi). Agentni qaytadan urining.")
                return
                
            thought = data.get("thought", "")
            tool = data.get("tool", "done")
            tool_args = data.get("tool_args", {})
            answer = data.get("answer", "")
            
            # Agar 'done' bo'lsa tugatamiz
            if tool == "done":
                await wait.edit_text(f"🤖 **Agent:**\n\n{answer}")
                return
                
            # Asbobni ishlatish jarayoni haqida xabar berish
            await wait.edit_text(f"🤖 **Agent (Qadam {step+1}):**\n💭 {thought}\n🛠️ Tool: `{tool}`\nIsh bajarilmoqda...")
            
            tool_result = ""
            if tool == "send_message":
                peer_name = tool_args.get("peer")
                text_msg = tool_args.get("text")
                if not peer_name or not text_msg:
                    tool_result = "Xatolik: peer yoki text parametri yo'q."
                else:
                    peer = await userbot.search_peer(peer_name)
                    if peer:
                        try:
                            await userbot.send_message(peer, text_msg)
                            tool_result = f"Xabar {peer} ga yuborildi."
                        except Exception as e:
                            tool_result = f"Xatolik: {e}"
                    else:
                        tool_result = f"Xatolik: '{peer_name}' topilmadi."
                    
            elif tool == "ask_telegram_bot":
                bot_username = tool_args.get("bot_username")
                question = tool_args.get("question")
                if not bot_username or not question:
                    tool_result = "Xatolik: bot_username yoki question parametri yo'q."
                else:
                    tool_result = await userbot.ask_ai_bot(bot_username, question)
                
            elif tool == "execute_telethon":
                code = tool_args.get("code")
                if not code:
                    tool_result = "Xatolik: code parametri yo'q."
                else:
                    tool_result = await userbot.execute_telethon_code(code)
                
            else:
                tool_result = f"Noma'lum tool chaqirildi: {tool}"
                
            # Tarixga qo'shamiz
            conversation_history += f"\n- Qadam {step+1}: {tool} ishlatildi.\n- Natija: {tool_result}"
            
        except Exception as e:
            log.error(f"Agent loop error: {e}")
            await wait.edit_text(f"❌ Ichki xatolik yuz berdi: {e}")
            return
            
    await wait.edit_text("⚠️ Agent maksimal qadamlar soniga yetdi (muammo murakkab ko'rinadi). Qisman bajargan bo'lishi mumkin.")
