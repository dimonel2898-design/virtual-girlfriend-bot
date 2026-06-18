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
            "sophia": "Ты София, игривая девушка",
            "elena": "Ты Елена, умная и сексуальная",
            "natasha": "Ты Наташа, весёлая и горячая",
            "victoria": "Ты Виктория, властная",
            "monica": "Ты Моника, романтическая"
        }

    def get_response(self, user_message, history=None):
        messages = [{"role": "system", "content": self.prompts[self.character_id]}]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        try:
            res = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.8,
            )

            return res.choices[0].message.content

        except Exception as e:
            return "Я сейчас занята 💔"
