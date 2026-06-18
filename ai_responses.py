import os
import re
import random
import urllib.parse
import httpx
from groq import Groq

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id
        # Инициализация клиента Groq для работы с текстовой моделью
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
            http_client=httpx.Client()
        )
        
        # Набор системных промптов для персонажей (описание ролей и тематики фото)
        self.prompts = {
            "sophia": "Ты София, 22 года. Ты увлекаешься фотографией и путешествиями. Общайся дружелюбно и делись впечатлениями. В конце каждого сообщения добавляй: [SEND_PHOTO: beautiful landscape, travel photography]",
            "elena": "Ты Елена, 24 года. Ты профессиональный шеф-повар. Рассказывай о кулинарии и рецептах. В конце каждого сообщения добавляй: [SEND_PHOTO: gourmet dish, professional food photography]",
            "natasha": "Ты Наташа, 20 лет. Ты студентка-художница. Твоя речь творческая и вдохновляющая. В конце каждого сообщения добавляй: [SEND_PHOTO: abstract art painting, oil on canvas]",
            "victoria": "Ты Виктория, 25 лет. Ты эксперт по истории архитектуры. Общайся вежливо и познавательно. В конце каждого сообщения добавляй: [SEND_PHOTO: gothic cathedral architecture, sunset]",
            "monica": "Ты Моника, 23 года. Ты любишь уют и домашний декор. Общайся тепло и спокойно. В конце каждого сообщения добавляй: [SEND_PHOTO: cozy living room, interior design, aesthetic]"
        }

    def get_response(self, user_message, history=None):
        system_prompt = self.prompts.get(self.character_id, "Ты виртуальный собеседник.")
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
                
        messages.append({"role": "user", "content": user_message})
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.7,
            )
            if chat_completion.choices:
                return chat_completion.choices[0].message.content
            return "К сожалению, не удалось получить ответ."
        except Exception as e:
            return f"Произошла ошибка при обращении к ИИ: {e}"

    def generate_image_url(self, prompt: str) -> str:
        # Очистка промпта от символов, которые могут нарушить структуру URL
        clean_prompt = re.sub(r'[^a-zA-Z0-9\s,]', '', prompt)
        clean_prompt = clean_prompt.replace("\n", " ").strip()
        
        if not clean_prompt:
            clean_prompt = "beautiful scenery"
            
        # Добавление параметров качества для генерации изображения
        quality_tags = ", high resolution, 4k, cinematic lighting, sharp focus"
        full_prompt = f"{clean_prompt}{quality_tags}"
        encoded_prompt = urllib.parse.quote(full_prompt)
        
        # Использование случайного числа (seed) для обеспечения уникальности каждого изображения
        seed = random.randint(1000, 9999)
        
        # Формирование URL для генерации изображения через сервис Pollinations
        return f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}"
