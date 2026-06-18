async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        char_id = context.user_data.get("char", "sophia")
        ai = CharacterAI(char_id)

        user_text = update.message.text
        history = context.user_data.get("history", [])

        # Получаем текстовый ответ от ИИ модели Llama
        response = ai.get_response(user_text, history)

        # Сохраняем сообщения в историю контекста чата
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": response})
        context.user_data["history"] = history[-8:]

        # Сокращенные корни триггеров, чтобы ловить любые опечатки и падежи
        photo_triggers = ["фот", "снимок", "селфи", "выгляди", "покажи", "купальник", "купальнике"]
        user_text_lower = user_text.lower()

        # Сначала ВСЕГДА отправляем текстовый ответ ИИ
        await update.message.reply_text(response)

        # Проверяем, содержит ли текст пользователя запрос на фото
        if any(trigger in user_text_lower for trigger in photo_triggers):
            try:
                # Включаем анимацию "отправка фото" в интерфейсе Telegram
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
                
                # Извлекаем базовое описание внешности из ai_responses.py
                if hasattr(ai, "get_image_prompt"):
                    base_prompt = ai.get_image_prompt()
                else:
                    base_prompt = "A beautiful 22-year-old playful girl, cute smile, blonde hair, casual stylish clothes, photorealistic, 4k"
                
                # Если пользователь попросил купальник, точечно меняем описание одежды на бикини и пляж
                if "купальник" in user_text_lower or "купальнике" in user_text_lower:
                    base_prompt = base_prompt.replace("casual stylish clothes", "wearing a bikini on a tropical beach")
                    base_prompt = base_prompt.replace("office blouse", "wearing a bikini on a tropical beach")
                    base_prompt = base_prompt.replace("crop top, leather jacket", "wearing a bikini on a tropical beach")
                    base_prompt = base_prompt.replace("luxury business suit, rich interior background", "wearing a bikini on a tropical beach")
                    base_prompt = base_prompt.replace("summer dress, holding a flower, sunny park background", "wearing a bikini on a tropical beach")
                    if "bikini" not in base_prompt:
                        base_prompt += ", wearing a bikini on a beautiful beach background"

                # Генерируем случайный seed
                seed = random.randint(1, 999999)
                
                # ИСПРАВЛЕНО: Безопасное кодирование промпта без ломания DNS-имени хоста
                import urllib.parse
                encoded_prompt = urllib.parse.quote(base_prompt)
                photo_url = f"https://pollinations.ai{encoded_prompt}&seed={seed}&width=1024&height=1024&model=flux"
                
                # Скачиваем картинку в память сервера
                async with httpx.AsyncClient(timeout=45.0) as client:
                    img_response = await client.get(photo_url)
                    
                    if img_response.status_code == 200:
                        photo_bytes = img_response.content
                        
                        # Отправляем скачанные байты как готовое фото
                        await update.message.reply_photo(
                            photo=photo_bytes,
                            caption="📸 Лови моё фото! Как тебе? 😉"
                        )
                    else:
                        raise RuntimeError(f"Pollinations AI вернул статус-код: {img_response.status_code}")
                        
            except Exception as img_err:
                logger.error(f"Ошибка генерации или отправки картинки: {img_err}")
                await update.message.reply_text("💔 Ой, камера на телефоне что-то забарахлила... Попробуй ещё раз попросить?")
                
    except Exception as e:
        logger.error(f"Общая ошибка в handle_message: {e}")
        await update.message.reply_text("💔 Ошибка, попробуй ещё раз")
