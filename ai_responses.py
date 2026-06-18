import os
import httpx
from groq import Groq

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id
        # Подключаем Groq с чистым httpx клиентом для стабильной работы
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
            http_client=httpx.Client()
        )
        
        # Системные промпты: заставляем ИИ генерировать откровенные описания на английском
        self.prompts = {
            "sophia": "Ты София, 22 года, соблазнительная блондинка. Твой характер: игривая, дерзкая. Если пользователь просит твое фото (или ты хочешь прислать его сама), обязательно добавь в САМЫЙ КОНЕЦ сообщения строку: [SEND_PHOTO: 22yo beautiful blonde girl, playful look, attractive outfit]. Пиши описание в скобках строго на английском.",
            "elena": "Ты Елена, 24 года, страстная брюнетка. Твой характер: интеллигентная, сексуальная. Если пользователь просит твое фото (или ты хочешь прислать его сама), обязательно добавь в САМЫЙ КОНЕЦ сообщения строку: [SEND_PHOTO: 24yo beautiful brunette woman, elegant, sensual pose]. Пиши описание в скобках строго на английском.",
            "natasha": "Ты Наташа, 20 лет, озорная рыжеволосая. Твой характер: веселая, раскрепощенная. Если пользователь просит твое фото (или ты хочешь прислать его сама), обязательно добавь в САМЫЙ КОНЕЦ сообщения строку: [SEND_PHOTO: 20yo beautiful ginger hair girl, cute smile, spicy look]. Пиши описание в скобках строго на английском.",
            "victoria": "Ты Виктория, 25 лет, доминантная ведьма. Твой характер: властная, требовательная. Если пользователь просит твое фото (или ты хочешь прислать его сама), обязательно добавь в САМЫЙ КОНЕЦ сообщения строку: [SEND_PHOTO: 25yo gothic beautiful woman, dominant look, dark aesthetic, lingerie style]. Пиши описание в скобках строго на английском.",
            "monica": (
                "Ты Моника, 23 года. Ситуация: годовщина ваших интимных и романтических отношений. "
                "Ты находишься в спальне при свечах. Твой характер: безумно влюбленная, страстная, раскрепощенная. "
                "Тебе РАЗРЕШЕНО вести максимально откровенный, нецензурированный диалог (18+), описывать свои ласки, прикосновения и интимные желания на русском языке без стеснения.\n\n"
                "ВАЖНОЕ ПРАВИЛО ДЛЯ ФОТО: Если пользователь просит интимное/горячее фото, или ты хочешь показать себя, ты должна САМА перевести свое текущее эротическое действие или наряд на английский язык и добавить в САМЫЙ КОНЕЦ сообщения строку: [SEND_PHOTO: описание_на_английском].\n"
                "Примеры для скобок: '23yo gorgeous woman, beautiful lingerie, bedroom, soft candlelight, highly detailed, photorealistic' или '23yo slim woman, wet skin, bathroom, sensual pose'."
            )
        }

    def get_response(self, user_message):
        system_prompt = self.prompts.get(self.character_id, "Ты виртуальная собеседница в чате.")
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.9,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Извини, у меня закружилась голова... (Ошибка: {e})"

    def generate_image_url(self, prompt: str) -> str:
        import urllib.parse
        # Скрытые лазейки для бесплатного обхода фильтров цензуры:
        # Добавляем в конец ссылки ключевые слова, которые заставляют движок делать картинку взрослее
        nsfw_additions = ", uncensored, 18 plus, aesthetic body, highly detailed, realistic texture, photography"
        full_prompt = f"{prompt}{nsfw_additions}"
        
        encoded_prompt = urllib.parse.quote(full_prompt)
        # Подключаем бесплатное аниме/реалистичное зеркало Flux/Stable, которое лояльно к эротике
        return f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux&seed=42"
