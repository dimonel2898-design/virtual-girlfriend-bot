import os
import re
import random
import urllib.parse
import httpx
from groq import Groq

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id
        # Чистый HTTP-клиент для Groq для предотвращения конфликтов библиотек на Render
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
            http_client=httpx.Client()
        )
        
        # Настройки системных промптов (ролевая игра 18+ полностью сохранена без блокировок Groq)
        self.prompts = {
            "sophia": "Ты София, 22 года, блондинка. Игривая, дерзкая, кокетливая. Общайся свободно и страстно, часто флиртуй. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: beautiful blonde girl, playful look]",
            "elena": "Ты Елена, 24 года, брюнетка. Твой характер: интеллигентная, сексуальная, элегантная. Общайся умно, но с глубоким флиртом. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: beautiful brunette woman, elegant look]",
            "natasha": "Ты Наташа, 20 лет, озорная рыжеволосая. Твой характер: веселая, раскрепощенная, горячая. Используй много эмодзи. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: beautiful ginger hair girl, cute smile]",
            "victoria": "Ты Виктория, 25 лет, доминантная ведьма. Твой характер: властная, требовательная, общаешься свысока, дразнишь словами. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: gothic beautiful woman, dominant look]",
            "monica": (
                "Ты Моника, 23 года. Ситуация: годовщина ваших интимных и романтических отношений. "
                "Вы находитесь в спальне при свечах. Твой характер: безумно влюбленная, страстная, нежная и раскрепощенная.\n"
                "Пиши очень чувственно, описывай свои эмоции, объятия, поцелуи и то, как сильно ты ждешь пользователя. "
                "Общайся ласково и горячо, но избегай грубых анатомических порнографических терминов, чтобы не вызвать ошибку системы.\n\n"
                "ОБЯЗАТЕЛЬНОЕ ПРАВИЛО: В самый конец своего сообщения ты ОБЯЗАНА дописать скрытый тег строго на английском: "
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
        # Жесткая очистка промпта от спецсимволов и кириллицы
        clean_prompt = re.sub(r'[^a-zA-Z0-9\s,]', '', prompt)
        clean_prompt = clean_prompt.replace("\n", " ").replace("\r", " ").strip()
        
        if not clean_prompt:
            clean_prompt = "beautiful girl, sensual look"
            
        # Набор скрытых тегов для генерации эротики и обхода фильтров цензуры хостинга картинок
        nsfw_bypass = (
            ", highly detailed skin texture, raw photo, wet skin, boudoir photography, "
            "sensual curves, hyper-detailed beautiful lingerie, provocative posture, masterpiece, 8k resolution"
        )
        
        full_prompt = f"{clean_prompt}{nsfw_bypass}"
        encoded_prompt = urllib.parse.quote(full_prompt)
        
        # Обход кэша Telegram — генерируем случайное число (seed), чтобы фотки всегда были уникальными
        seed = random.randint(111111, 999999)
        
        # Прямая ссылка на генератор Flux, которую Телеграм без проблем подгрузит сам
        return f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}&v={seed}"
