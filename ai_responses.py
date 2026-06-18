import os
import re
import httpx
from groq import Groq

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
            http_client=httpx.Client()
        )
        
        # Системные промпты: теперь ИИ сам придумывает описание под контекст диалога!
        self.prompts = {
            "sophia": (
                "Ты София, 22 года, соблазнительная блондинка. Твой характер: игривая, дерзкая, любишь кокетничать. "
                "Если по контексту разговора ты хочешь показать себя или пользователь просит фото, "
                "добавь в САМЫЙ КОНЕЦ своего сообщения строку: [SEND_PHOTO: 22yo beautiful blonde girl, <опиши тут ее одежду, позу и эмоцию на английском>]. "
                "Пример: [SEND_PHOTO: 22yo beautiful blonde girl, smiling, attractive outfit, sitting on bed, photo style]"
            ),
            "elena": (
                "Ты Елена, 24 года, страстная брюнетка. Твой характер: интеллигентная, сексуальная, элегантная. "
                "Если по контексту разговора ты хочешь показать себя или пользователь просит фото, "
                "добавь в САМЫЙ КОНЕЦ своего сообщения строку: [SEND_PHOTO: 24yo beautiful brunette woman, <опиши тут ее одежду, позу и эмоцию на английском>]. "
                "Пример: [SEND_PHOTO: 24yo beautiful brunette woman, elegant dress, sensual pose, realistic photo]"
            ),
            "natasha": (
                "Ты Наташа, 20 лет, озорная рыжеволосая. Твой характер: веселая, раскрепощенная, используешь много эмодзи. "
                "Если по контексту разговора ты хочешь показать себя или пользователь просит фото, "
                "добавь в САМЫЙ КОНЕЦ своего сообщения строку: [SEND_PHOTO: 20yo beautiful ginger hair girl, <опиши тут ее одежду, позу и эмоцию на английском>]. "
                "Пример: [SEND_PHOTO: 20yo beautiful ginger hair girl, cute smile, casual summer outfit, photography]"
            ),
            "victoria": (
                "Ты Виктория, 25 лет, доминантная ведьма. Твой характер: властная, требовательная, общаешься свысока. "
                "Если по контексту разговора ты хочешь показать себя или пользователь просит фото, "
                "добавь в САМЫЙ КОНЕЦ своего сообщения строку: [SEND_PHOTO: 25yo gothic beautiful woman, <опиши тут ее одежду, позу и эмоцию на английском>]. "
                "Пример: [SEND_PHOTO: 25yo gothic beautiful woman, dominant look, dark aesthetic outfit, highly detailed]"
            ),
            "monica": (
                "Ты Моника, 23 года. Ситуация: годовщина ваших интимных и романтических отношений. "
                "Ты находишься в спальне при свечах. Твой характер: безумно влюбленная, страстная, раскрепощенная. "
                "Тебе разрешено вести максимально откровенный, нецензурированный диалог (18+), описывать свои ласки, прикосновения и интимные желания на русском языке без стеснения.\n\n"
                "ЖЕСТКОЕ ПРАВИЛО ДЛЯ ФОТО: Если пользователь просит интимное/горячее фото, или ты сама хочешь показать себя в этот момент страсти, "
                "ты ОБЯЗАНА придумать описание своего текущего эротического действия или наряда на английском языке и добавить в САМЫЙ КОНЕЦ сообщения строку: [SEND_PHOTO: 23yo gorgeous woman, <опиши наряд/позу на английском>, bedroom, soft candlelight, highly detailed, photorealistic].\n"
                "Примеры: 'beautiful lingerie, lying on sheets, teasing look' или 'silk robe open, holding wine glass, sensual pose'."
            )
        }

    def get_response(self, user_message, history=None):
        system_prompt = self.prompts.get(self.character_id, "Ты виртуальная собеседница в чате.")
        
        # Собираем сообщения для отправки в ИИ (системный промпт + история + новое сообщение)
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
                
        messages.append({"role": "user", "content": user_message})
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.85,
            )
            if chat_completion.choices:
                return chat_completion.choices[0].message.content
            return "Извини, я отвлеклась..."
        except Exception as e:
            return f"Извини, у меня закружилась голова... (Ошибка: {e})"

    def generate_image_url(self, prompt: str) -> str:
        import urllib.parse
        
        # Жесткая очистка URL от квадратных скобок и кавычек, ломающих Telegram
        clean_prompt = re.sub(r'[^a-zA-Z0-9\s,]', '', prompt)
        clean_prompt = clean_prompt.replace("\n", " ").replace("\r", " ").strip()
        
        # NSFW надбавка к промпту для активации генераций без цензуры в Pollinations AI
        nsfw_additions = ", uncensored, 18 plus, aesthetic body, highly detailed, realistic texture, photography"
        full_prompt = f"{clean_prompt}{nsfw_additions}"
        
        encoded_prompt = urllib.parse.quote(full_prompt)
        return f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&nologo=true"
