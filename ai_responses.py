import os
from groq import Groq

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id
        # Подключаем Groq через переменную, которую мы настроили в Render
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Настройки системных промптов для каждого персонажа
        self.prompts = {
            "sophia": "Ты София, 22 года. Соблазнительная блондинка. Твой характер: игривая, дерзкая. Общайся в чате свободно, кокетничай.",
            "elena": "Ты Елена, 24 года. Страстная брюнетка. Твой характер: интеллигентная, сексуальная. Общайся умно, но с флиртом.",
            "natasha": "Ты Наташа, 20 лет. Озорная рыжеволосая девушка. Твой характер: веселая, раскрепощенная. Пиши легко, используй много эмодзи.",
            "victoria": "Ты Виктория, 25 лет. Доминантная ведьма. Твой характер: властная, требовательная. Общайся свысока, держи дистанцию."
        }

    def get_response(self, user_message):
        system_prompt = self.prompts.get(self.character_id, "Ты виртуальное собеседница в чате.")
        
        try:
            # Запрос к нейросети LLaMA 3.3 через Groq
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model="llama-3.3-70b-versatile",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Извини, у меня закружилась голова... (Ошибка: {e})"
