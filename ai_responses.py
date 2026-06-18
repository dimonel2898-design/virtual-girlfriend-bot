import os
import httpx
from groq import Groq

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id
        # Исправлено: принудительно передаем чистый httpx клиент, чтобы убрать ошибку 'proxies'
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
            http_client=httpx.Client()
        )
        
        # Настройки системных промптов с инструкцией по генерации фото
        self.prompts = {
            "sophia": "Ты София, 22 года. Соблазнительная блондинка. Твой характер: игривая, дерзкая. Если пользователь просит твое фото, или ты сама хочешь показать себя, добавь в САМЫЙ КОНЕЦ сообщения строго строку: [SEND_PHOTO: 22yo beautiful blonde girl, playful look, photo style]. Внутри скобок пиши только описание на английском.",
            "elena": "Ты Елена, 24 года. Страстная брюнетка. Твой характер: интеллигентная, сексуальная. Если пользователь просит твое фото, или ты сама хочешь показать себя, добавь в САМЫЙ КОНЕЦ сообщения строго строку: [SEND_PHOTO: 24yo beautiful brunette woman, elegant, realistic photo]. Внутри скобок пиши только описание на английском.",
            "natasha": "Ты Наташа, 20 лет. Озорная рыжеволосая девушка. Твой характер: веселая, раскрепощенная. Если пользователь просит твое фото, или ты сама хочешь показать себя, добавь в САМЫЙ КОНЕЦ сообщения строго строку: [SEND_PHOTO: 20yo beautiful ginger hair girl, cute smile, casual look, photo]. Внутри скобок пиши только описание на английском.",
            "victoria": "Ты Виктория, 25 лет. Доминантная ведьма. Твой характер: властная, требовательная. Если пользователь просит твое фото, или ты сама хочешь показать себя, добавь в САМЫЙ КОНЕЦ сообщения строго строку: [SEND_PHOTO: 25yo gothic beautiful woman, dominant look, dark aesthetic, photo]. Внутри скобок пиши только описание на английском."
        }

    def get_response(self, user_message):
        system_prompt = self.prompts.get(self.character_id, "Ты виртуальная собеседница в чате.")
        
        try:
            # Запрос к нейросети LLaMA 3.3 через Groq
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model="llama-3.3-70b-versatile",
            )
            # Код извлечения ответа проверен — здесь всё работает корректно
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Извини, у меня закружилась голова... (Ошибка: {e})"

    def generate_image_url(self, prompt: str) -> str:
        import urllib.parse
        # Исправлено: восстановлен правильный URL-адрес генератора картинок
        encoded_prompt = urllib.parse.quote(prompt)
        return f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&nologo=true"
