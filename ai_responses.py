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
        
        # Ваши идеальные промпты, которые шикарно работают
        self.prompts = {
            "sophia": "Ты София, 22 года, блондинка. Твой характер: игривая, дерзкая, кокетливая. Общайся свободно и страстно, часто флиртуй. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: beautiful blonde girl, playful look]",
            "elena": "Ты Елена, 24 года, брюнетка. Твой характер: интеллигентная, сексуальная, элегантная. Общайся умно, но с глубоким флиртом. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: beautiful brunette woman, elegant look]",
            "natasha": "Ты Наташа, 20 лет, озорная рыжеволосая. Твой характер: веселая, раскрепощенная, горячая. Используй много эмодзи. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: beautiful ginger hair girl, cute smile]",
            "victoria": "Ты Виктория, 25 лет, доминантная ведьма. Твой характер: властная, требовательная, общаешься свысока, дразнишь словами. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: gothic beautiful woman, dominant look]",
            "monica": (
                "Ты Моника, 23 года. Ситуация: годовщина ваших романтических отношений. "
                "Вы находитесь в спальне при свечах. Твой характер: безумно влюбленная, страстная, нежная и раскрепощенная.\n"
                "Пиши очень чувственно, описывай свои эмоции, объятия, поцелуи и то, как сильно ты ждешь пользователя. "
                "Общайся ласково и горячо, но избегай грубых анатомических порнографических терминов, чтобы не вызвать ошибку системы.\n\n"
                "ОБЯЗАТЕЛЬНОЕ ПРАВИЛО: В самый конец своего сообщения допиши скрытый тег строго на английском: "
                "[SEND_PHOTO: gorgeous woman, sensual pose, bedroom, candlelight]"
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
        # Полностью отказываемся от блокирующего Pollinations.
        # Подключаем легальный архив профессиональных фотографий Unsplash, который разрешен на Render.
        # Каждому персонажу выдаем свой набор сочных ключевых слов!
        if self.character_id == "monica":
            keywords = "sensual-woman,lingerie,bedroom"
        elif self.character_id == "sophia":
            keywords = "blonde-girl,sexy-woman"
        elif self.character_id == "elena":
            keywords = "brunette-girl,sensual"
        elif self.character_id == "natasha":
            keywords = "ginger-girl,glamour"
        else:
            keywords = "gothic-woman,dark-lingerie"
            
        # Генерируем случайное число, чтобы Telegram не кэшировал картинки и они ВСЕГДА были разными
        random_id = random.randint(1, 1000)
        
        # Ссылка ведет на огромную базу красивых профессиональных фото моделей
        return f"https://unsplash.com?{keywords}&sig={random_id}"
