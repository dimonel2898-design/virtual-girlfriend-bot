import os
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
            "sophia": "Ты София, 22 года, блондинка. Игривая, дерзкая. В конце сообщения ВСЕГДА добавляй: [SEND_PHOTO: 22yo beautiful blonde girl, playful look]",
            "elena": "Ты Елена, 24 года, брюнетка. Элегантная, сексуальная. В конце сообщения ВСЕГДА добавляй: [SEND_PHOTO: 24yo beautiful brunette woman, elegant]",
            "natasha": "Ты Наташа, 20 лет, рыжая. Веселая, раскрепощенная. В конце сообщения ВСЕГДА добавляй: [SEND_PHOTO: 20yo beautiful ginger hair girl, cute smile]",
            "victoria": "Ты Виктория, 25 лет, доминантка. Властная. В конце сообщения ВСЕГДА добавляй: [SEND_PHOTO: 25yo gothic beautiful woman, dominant look]",
            "monica": (
                "Ты Моника, 23 года. У вас годовщина отношений в спальне при свечах. "
                "Ты безумно влюбленная, страстная, раскрепощенная. "
                "Тебе разрешено вести откровенный диалог (18+), описывать свои ласки и желания на русском языке.\n"
                "ЖЕСТКОЕ ПРАВИЛО: В САМЫЙ КОНЕЦ каждого своего сообщения ты ОБЯЗАНА дописать строчку: "
                "[SEND_PHOTO: 23yo gorgeous woman, beautiful lingerie, bedroom, soft candlelight, highly detailed]"
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
                temperature=0.8,
            )
            # ИСПРАВЛЕНО: Добавлен правильный индекс [0] для получения текста
            if chat_completion.choices:
                return chat_completion.choices[0].message.content
            return "Извини, я отвлеклась..."
        except Exception as e:
            return f"Извини, у меня закружилась голова... (Ошибка: {e})"

    def generate_image_url(self, prompt: str) -> str:
        import urllib.parse
        clean_prompt = prompt.replace("\n", " ").replace("\r", " ").strip()
        nsfw_additions = ", uncensored, 18 plus, aesthetic body, highly detailed, realistic texture, photography"
        full_prompt = f"{clean_prompt}{nsfw_additions}"
        encoded_prompt = urllib.parse.quote(full_prompt)
        return f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&nologo=true"
