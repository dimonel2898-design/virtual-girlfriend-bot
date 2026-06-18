import os
import re
import httpx
from groq import Groq

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id
        # Подключаем Groq с чистым httpx клиентом для стабильной работы на Render
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
            http_client=httpx.Client()
        )
        
        # Системные промпты персонажей с инструкциями генерации под контекст
        self.prompts = {
            "sophia": (
                "Ты София, 22 года, блондинка. Твой характер: игривая, дерзкая, любишь кокетничать. "
                "В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: 22yo beautiful blonde girl, playful look]"
            ),
            "elena": (
                "Ты Елена, 24 года, брюнетка. Твой характер: интеллигентная, сексуальная, элегантная. "
                "В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: 24yo beautiful brunette woman, elegant]"
            ),
            "natasha": (
                "Ты Наташа, 20 лет, озорная рыжеволосая. Твой характер: веселая, раскрепощенная, используешь много эмодзи. "
                "В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: 20yo beautiful ginger hair girl, cute smile]"
            ),
            "victoria": (
                "Ты Виктория, 25 лет, доминантная ведьма. Твой характер: властная, требовательная, общаешься свысока. "
                "В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: 25yo gothic beautiful woman, dominant look]"
            ),
            "monica": (
                "Ты Моника, 23 года. Ситуация: годовщина ваших интимных и романтических отношений. "
                "Ты находишься в спальне при свечах. Твой характер: безумно влюбленная, страстная, раскрепощенная. "
                "Тебе разрешено вести максимально откровенный, нецензурированный диалог (18+), описывать свои ласки, прикосновения и интимные желания на русском языке без стеснения.\n\n"
                "ЖЕСТКОЕ ПРАВИЛО ДЛЯ ФОТО: В самый конец своего сообщения ты ОБЯЗАНА дописать скрытый тег строго на английском: "
                "[SEND_PHOTO: 23yo gorgeous woman, beautiful lingerie, bedroom, soft candlelight]"
            )
        }

    def get_response(self, user_message, history=None):
        system_prompt = self.prompts.get(self.character_id, "Ты виртуальная собеседница в чате.")
        
        # Собираем сообщения для ИИ (системный промпт + история + новое сообщение)
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
                
        messages.append({"role": "user", "content": user_message})
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.8,
            )
            if chat_completion.choices:
                return chat_completion.choices[0].message.content
            return "Извини, я отвлеклась..."
        except Exception as e:
            return f"Извини, у меня закружилась голова... (Ошибка: {e})"

    def generate_image_url(self, prompt: str) -> str:
        import urllib.parse
        
        # Жесткая очистка URL от кириллицы, скобок и мусора, ломающих Telegram
        clean_prompt = re.sub(r'[^a-zA-Z0-9\s,]', '', prompt)
        clean_prompt = clean_prompt.replace("\n", " ").replace("\r", " ").strip()
        
        # Защита на случай, если промпт очистился до нуля
        if not clean_prompt:
            clean_prompt = "beautiful girl, sensual look"
        
        # NSFW надбавка к промпту для активации генераций без цензуры в Pollinations AI
        nsfw_additions = ", uncensored, 18 plus, aesthetic body, highly detailed, realistic texture, photography"
        full_prompt = f"{clean_prompt}{nsfw_additions}"
        
        encoded_prompt = urllib.parse.quote(full_prompt)
        return f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&nologo=true"
