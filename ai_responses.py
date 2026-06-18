import os
import re
import random
import urllib.parse
import httpx
from groq import Groq

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id
        # Чистый HTTP-клиент для Groq
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
            http_client=httpx.Client()
        )
        
        # Системные промпты (оставляем твою идеальную настройку ролевой игры 18+)
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
                temperature=0.85,
            )
            if chat_completion.choices and len(chat_completion.choices) > 0:
                return chat_completion.choices[0].message.content
            return "Извини, я немного отвлеклась..."
        except Exception as e:
            return f"Извини, у меня закружилась голова... (Ошибка: {e})"

    def generate_image_url(self, prompt: str) -> str:
        # Полностью отказываемся от капризного Pollinations.
        # Переключаемся на глобальную базу высококачественных фото Source Unsplash.
        # Генерируем случайный сид, чтобы при каждой реплике Моника слала РАЗНЫЕ горячие фотки!
        random_seed = random.randint(111, 99999)
        
        # Определяем тему картинок для каждого персонажа отдельно
        if self.character_id == "monica":
            keywords = "sensual,girl,lingerie,bedroom"
        elif self.character_id == "sophia":
            keywords = "blonde,girl,sexy"
        elif self.character_id == "elena":
            keywords = "brunette,woman,sensual"
        elif self.character_id == "natasha":
            keywords = "ginger,girl,boudoir"
        else:
            keywords = "gothic,woman,lingerie"
            
        # Этот URL отдает реальные фотографии без блокировок, и сервер Render сможет скачать его за 1 секунду
        return f"https://unsplash.com{random_seed}&keywords={keywords}"
