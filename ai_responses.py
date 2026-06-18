import os

class CharacterAI:
    def __init__(self, character_id):
        self.character_id = character_id

    def get_response(self, message):
        responses = {
            "sophia": f"Привет 😊 Ты написал: {message}",
            "elena": f"Интересно... Расскажи подробнее: {message}",
            "natasha": f"Ха-ха 😄 {message}",
            "victoria": f"Я внимательно слушаю тебя. {message}",
        }

        return responses.get(
            self.character_id,
            f"Неизвестный персонаж: {message}"
        )
