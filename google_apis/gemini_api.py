"""
Gemini API — AI chat va Audio→Text
google-generativeai kutubxonasi ishlatiladi
"""
import asyncio
import base64
import logging
import os
from pathlib import Path

log = logging.getLogger("gemini")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    log.warning("google-generativeai o'rnatilmagan. `pip install google-generativeai`")


class GeminiAPI:
    def __init__(self):
        self._chat_model = None
        self._vision_model = None
        self._configured = False

    def setup(self, api_key: str):
        if not GEMINI_AVAILABLE:
            return False
        try:
            genai.configure(api_key=api_key)
            # Use gemini-2.0-flash
            self._chat_model = genai.GenerativeModel("gemini-2.0-flash")
            self._vision_model = genai.GenerativeModel("gemini-2.0-flash")
            self._configured = True
            log.info("✅ Gemini API ulandi.")
            return True
        except Exception as e:
            log.error(f"Gemini setup xatosi: {e}")
            return False

    def is_available(self) -> bool:
        return GEMINI_AVAILABLE and self._configured

    # ─── TEXT CHAT ────────────────────────────────────────────

    async def ask(self, question: str, system_prompt: str = None) -> str:
        """Matn savoliga javob beradi"""
        if not self.is_available():
            return "⚠️ Gemini API sozlanmagan. GEMINI_API_KEY ni kiriting."

        loop = asyncio.get_event_loop()
        try:
            prompt = question
            if system_prompt:
                prompt = f"{system_prompt}\n\nSavol: {question}"

            response = await loop.run_in_executor(
                None,
                lambda: self._chat_model.generate_content(prompt)
            )
            return response.text
        except Exception as e:
            log.error(f"Gemini ask xatosi: {e}")
            return f"❌ Gemini xatosi: {e}"

    async def agent_ask(self, question: str, system_prompt: str) -> str:
        """Agent uchun JSON qaytaruvchi metod"""
        if not self.is_available():
            return '{"action": "error", "message": "Gemini API sozlanmagan"}'
        
        loop = asyncio.get_event_loop()
        try:
            prompt = f"{system_prompt}\n\nQuyidagi matn asosida qaror qabul qil va FAQAT aniq JSON formatida qaytar (Markdown backticks ishlatma, to'g'ridan-to'g'ri JSON qaytar):\n\nSavol/Buyruq: {question}"
            
            # Using generation_config for JSON if supported, else fallback to prompt instruction
            try:
                model = genai.GenerativeModel("gemini-2.0-flash", generation_config={"response_mime_type": "application/json"})
                response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
                return response.text
            except Exception as e_json:
                log.warning(f"JSON mime type error, falling back: {e_json}")
                response = await loop.run_in_executor(None, lambda: self._chat_model.generate_content(prompt))
                text = response.text
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                return text.strip()
                
        except Exception as e:
            log.error(f"Gemini agent_ask xatosi: {e}")
            return '{"action": "error", "message": "API xatosi"}'

    # ─── AUDIO → TEXT ─────────────────────────────────────────

    async def audio_to_text(self, audio_path: str) -> str:
        """Audio faylni matnга aylantiradi (Whisper o'rniga)"""
        if not self.is_available():
            return "⚠️ Gemini API sozlanmagan."

        loop = asyncio.get_event_loop()
        try:
            # Faylni o'qiymiz
            with open(audio_path, "rb") as f:
                audio_data = f.read()

            ext = Path(audio_path).suffix.lower()
            mime_map = {
                ".ogg": "audio/ogg",
                ".mp3": "audio/mpeg",
                ".wav": "audio/wav",
                ".m4a": "audio/mp4",
                ".flac": "audio/flac",
            }
            mime_type = mime_map.get(ext, "audio/ogg")

            audio_part = {
                "mime_type": mime_type,
                "data": base64.b64encode(audio_data).decode()
            }

            response = await loop.run_in_executor(
                None,
                lambda: self._vision_model.generate_content([
                    audio_part,
                    "Ushbu audio yozuvni aniq va to'liq matnга aylantir. Faqat matni yoz, boshqa hech narsa yozma."
                ])
            )
            return response.text

        except Exception as e:
            log.error(f"Audio→Text xatosi: {e}")
            return f"❌ Audio o'girishda xato: {e}"

    # ─── IMAGE ANALYSIS ───────────────────────────────────────

    async def analyze_image(self, image_path: str, question: str = "Bu rasmda nima bor?") -> str:
        """Rasmni tahlil qiladi"""
        if not self.is_available():
            return "⚠️ Gemini API sozlanmagan."

        loop = asyncio.get_event_loop()
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()

            ext = Path(image_path).suffix.lower()
            mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                        ".png": "image/png", ".webp": "image/webp"}
            mime_type = mime_map.get(ext, "image/jpeg")

            image_part = {
                "mime_type": mime_type,
                "data": base64.b64encode(image_data).decode()
            }

            response = await loop.run_in_executor(
                None,
                lambda: self._vision_model.generate_content([image_part, question])
            )
            return response.text

        except Exception as e:
            log.error(f"Image analysis xatosi: {e}")
            return f"❌ Rasm tahlilida xato: {e}"

    # ─── SUMMARIZE ────────────────────────────────────────────

    async def summarize(self, text: str, lang: str = "uzbek") -> str:
        """Uzun matnni qisqartiradi"""
        prompt = f"Quyidagi matnni {lang} tilida qisqacha va aniq xulosa qilib ber:\n\n{text[:10000]}"
        return await self.ask(prompt)

    async def translate(self, text: str, to_lang: str = "uzbek") -> str:
        """Tarjima qiladi"""
        prompt = f"Quyidagi matnni {to_lang} tiliga tarjima qil, faqat tarjimani yoz:\n\n{text}"
        return await self.ask(prompt)


# Global instance
gemini = GeminiAPI()
