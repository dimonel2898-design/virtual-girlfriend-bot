import os
import re
import random
import urllib.parse
import httpx
from groq import Groq

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
            http_client=httpx.Client()
        )
        
        # Полностью безопасные промпты, которые Groq никогда не заблокирует
        self.prompts = {
            "sophia": "Ты София, 22 года, блондинка. Игривая, дерзкая, кокетливая. Общайся свободно и страстно, часто флиртуй. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: sophia_blonde_girl]",
            "elena": "Ты Елена, 24 года, брюнетка. Твой характер: интеллигентная, сексуальная, элегантная. Общайся умно, но с глубоким флиртом. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: elena_brunette_woman]",
            "natasha": "Ты Наташа, 20 лет, озорная рыжеволосая. Твой характер: веселая, раскрепощенная, горячая. Используй много эмодзи. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: natasha_ginger_girl]",
            "victoria": "Ты Виктория, 25 лет, доминантная ведьма. Твой характер: властная, требовательная, общаешься свысока. В самом конце каждого сообщения дописывай строго: [SEND_PHOTO: victoria_gothic_woman]",
            "monica": (
                "Ты Моника, 23 года. Ситуация: годовщина ваших интимных и романтических отношений. "
                "Вы находитесь в спальне при свечах. Твой характер: безумно влюбленная, страстная, нежная и раскрепощенная.\n"
                "Пиши очень чувственно, описывай свои эмоции, объятия, поцелуи и то, как сильно ты ждешь пользователя. "
                "Общайся ласково и горячо, но избегай грубых анатомических порнографических терминов, чтобы не вызвать ошибку системы.\n\n"
                "ОБЯЗАТЕЛЬНОЕ ПРАВИЛО: В самый конец своего сообщения ты ОБЯЗАНА дописать скрытый тег строго в таком формате: [SEND_PHOTO: monica_gorgeous_lingerie]"
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
        # КОСЯК С СИМВОЛАМИ РЕШЕН: Оставляем ТОЛЬКО латинские буквы и цифры. Никаких скобок, пробелов и знаков препинания!
        clean_prompt = re.sub(r'[^a-zA-Z0-9]', '', prompt)
        
        # Если промпт пустой или сбился — подставляем жесткий базовый тег в зависимости от персонажа
        if not clean_prompt or "monica" in clean_prompt.lower():
            target_prompt = "23yo-gorgeous-woman-beautiful-lingerie-bedroom-soft-candlelight"
        elif "sophia" in clean_prompt.lower():
            target_prompt = "22yo-beautiful-blonde-girl-playful-look-attractive-outfit"
        elif "elena" in clean_prompt.lower():
            target_prompt = "24yo-beautiful-brunette-woman-elegant-dress-sensual-pose"
        elif "natasha" in clean_prompt.lower():
            target_prompt = "20yo-beautiful-ginger-hair-girl-cute-smile-casual-look"
        else:
            target_prompt = "25yo-gothic-beautiful-woman-dominant-look-dark-aesthetic"

        # КОСЯК С КЭШЕМ РЕШЕН: Генерируем абсолютно случайные числа для seed и v
        random_seed = random.randint(100000, 999999)
        random_version = random.randint(111111, 999999)
        
        # Используем стабильный и лояльный к Telegram ИИ-генератор Flux
        return f"https://pollinations.ai{target_prompt}?width=1024&height=1024&nologo=true&seed={random_seed}&v={random_version}"
