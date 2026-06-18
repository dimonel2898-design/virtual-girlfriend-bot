import os
from groq import Groq
import httpx

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY"),
            http_client=httpx.Client()
        )

        self.prompts = {
            "sophia": "Ты София, игривая и кокетливая девушка",
            "elena": "Ты Елена, умная и сексуальная",
            "natasha": "Ты Наташа, веселая и горячая",
            "victoria": "Ты Виктория, властная",
            "monica": "Ты Моника, романтичная"
        }

    def get_response(self, message, history=None):
        try:
            messages = [{"role": "system", "content": self.prompts.get(self.character_id)}]

            if history:
                messages.extend(history[-8:])

            messages.append({"role": "user", "content": message})

            res = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.8,
            )

            return res.choices[0].message.content.strip()

        except Exception:
            return "💔 Я сейчас занята"
