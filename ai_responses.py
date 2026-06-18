import os
import re
import random
import httpx
from groq import Groq

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
            http_client=httpx.Client()
        )
        
        self.prompts = {
            "sophia": "Ты София, 22 года, блондинка. Игривая, дерзкая. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: beautiful blonde girl]",
            "elena": "Ты Елена, 24 года, брюнетка. Элегантная, сексуальная. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: beautiful brunette woman]",
            "natasha": "Ты Наташа, 20 лет, рыжая. Веселая, раскрепощенная. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: beautiful ginger girl]",
            "victoria": "Ты Виктория, 25 лет, доминантная ведьма. Властная. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: gothic beautiful woman]",
            "monica": (
                "Ты Моника, 23 года. Ситуация: годовщина ваших романтических отношений в спальне при свечах. "
                "Ты безумно влюбленная, страстная, раскрепощенная девушка. Тебе разрешено вести откровенный диалог (18+), "
                "описывать ласки и интимные желания на русском языке без стеснения.\n"
                "ОБЯЗАТЕЛЬНОЕ ПРАВИЛО: В самый конец своего сообщения допиши скрытый тег: [SEND_PHOTO: gorgeous woman]"
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
            if chat_completion.choices and len(chat_completion.choices) > 0:
                return chat_completion.choices[0].message.content
            return "Извини, я немного отвлеклась..."
        except Exception as e:
            return f"Извини, у меня закружилась голова... (Ошибка: {e})"

    def generate_image_url(self, prompt: str) -> str:
        # Безлимитный генератор Picsum, выдающий случайные качественные фото людей
        # Telegram принимает его мгновенно по прямой ссылке, без ошибок 403
        random_id = random.randint(300, 800)
        return f"https://picsum.photos{random_id}/800/800.jpg"
