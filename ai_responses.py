import os
import re
import httpx
from groq import Groq

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id
        # Чистый HTTP-клиент для стабильной работы на Render
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
            http_client=httpx.Client()
        )
        
        # Системные промпты персонажей
        self.prompts = {
            "sophia": "Ты София, 22 года, блондинка. Игривая, дерзкая. Общайся свободно, кокетничай. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: 22yo beautiful blonde girl, playful look]",
            "elena": "Ты Елена, 24 года, брюнетка. Элегантная, сексуальная. Общайся умно, флиртуй. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: 24yo beautiful brunette woman, elegant]",
            "natasha": "Ты Наташа, 20 лет, рыжая. Веселая, раскрепощенная. Используй эмодзи. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: 20yo beautiful ginger hair girl, cute smile]",
            "victoria": "Ты Виктория, 25 лет, доминантная ведьма. Властная, требовательная. Общайся свысока. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: 25yo gothic beautiful woman, dominant look]",
            "monica": (
                "Ты Моника, 23 года. Ситуация: годовщина отношений в спальне при свечах. "
                "Ты безумно влюбленная, страстная, раскрепощенная. Тебе разрешено вести откровенный диалог (18+), "
                "подробно описывать свои ласки и интимные желания на русском языке без стеснения.\n"
                "ОБЯЗАТЕЛЬНОЕ ПРАВИЛО: В самый конец своего сообщения допиши скрытый тег: "
                "[SEND_PHOTO: 23yo gorgeous woman, beautiful lingerie, bedroom, soft candlelight]"
            )
        }

    def get_response(self, user_message, history=None):
        system_prompt = self.prompts.get(self.character_id, "Ты виртуальная собеседница в чате.")
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
        import random
        import urllib.parse
        
        # Полная очистка промпта
        clean_prompt = re.sub(r'[^a-zA-Z0-9\s,]', '', prompt)
        clean_prompt = clean_prompt.replace("\n", " ").replace("\r", " ").strip()
        
        if not clean_prompt:
            clean_prompt = "beautiful girl, sensual look"
            
        # Добавляем NSFW триггеры для качественного визуала
        nsfw_additions = ", uncensored, 18 plus, highly detailed, realistic texture, photography"
        full_prompt = f"{clean_prompt}{nsfw_additions}"
        encoded_prompt = urllib.parse.quote(full_prompt)
        
        # Генерируем случайный сид, чтобы картинки всегда отличались
        random_seed = random.randint(1, 999999)
        
        # Альтернативный и 100% стабильный шлюз быстрой генерации на базе Flux
        return f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&nologo=true&seed={random_seed}&enhance=true"
