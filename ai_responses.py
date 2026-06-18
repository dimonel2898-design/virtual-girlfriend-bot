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

        # Текстовые системные промпты для чата
        self.prompts = {
            "sophia": "Ты София, игривая и кокетливая девушка. Часто флиртуешь и используешь смайлики.",
            "elena": "Ты Елена, умная, начитанная и сексуальная девушка.",
            "natasha": "Ты Наташа, веселая, открытая и горячая тусовщица.",
            "victoria": "Ты Виктория, властная, строгая и уверенная в себе доминантная девушка.",
            "monica": "Ты Моника, глубоко романтичная, нежная и чувственная натура."
        }

        # Описания внешности на английском (для нейросети генерации картинок)
        self.image_prompts = {
            "sophia": "A beautiful 22-year-old playful girl, cute smile, blonde hair, casual stylish clothes, photorealistic, 4k, cinematic lighting",
            "elena": "A stunning 25-year-old smart looking woman, elegant glasses, brunette tied hair, office blouse, seductive look, photorealistic, 4k",
            "natasha": "A gorgeous 23-year-old energetic girl, bright ginger hair, crop top, leather jacket, night club background, photorealistic, 4k",
            "victoria": "A beautiful 27-year-old powerful woman, strict look, dark hair, luxury business suit, rich interior background, photorealistic, 4k",
            "monica": "A lovely 21-year-old romantic girl, long wavy brown hair, summer dress, holding a flower, sunny park background, photorealistic, 4k"
        }

    def get_image_prompt(self):
        # Метод возвращает описание внешности текущего персонажа
        return self.image_prompts.get(self.character_id, "A beautiful young woman, photorealistic, 4k")

    def get_response(self, message, history=None):
        try:
            messages = [{"role": "system", "content": self.prompts.get(self.character_id, "Ты классная девушка")}]

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

