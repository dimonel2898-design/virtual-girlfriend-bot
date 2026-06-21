import os
import logging
import random
import urllib.parse
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import InvalidToken

from ai_responses import CharacterAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- ENV ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secret")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# ---------------- TELEGRAM APP ----------------
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден в ENV")

tg_app = Application.builder().token(BOT_TOKEN).build()

# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot V3.1 is running")

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

        # Сокращенные корни триггеров для фото (поймет любые опечатки)
        photo_triggers = ["фот", "снимок", "селфи", "выгляди", "покажи", "купальник", "купальнике"]
        user_text_lower = user_text.lower()

        # Сначала ВСЕГДА отправляем текстовый ответ ИИ
        await update.message.reply_text(response)

        # Проверяем запрос на фото
        if any(trigger in user_text_lower for trigger in photo_triggers):
            try:
                # Извлекаем базовое описание внешности из ai_responses.py
                if hasattr(ai, "get_image_prompt"):
                    base_prompt = ai.get_image_prompt()
                else:
                    base_prompt = "A beautiful 22-year-old playful girl, cute smile, blonde hair, casual stylish clothes, photorealistic, 4k"
                
                # Если пользователь попросил купальник
                if "купальник" in user_text_lower or "купальнике" in user_text_lower:
                    base_prompt = base_prompt.replace("casual stylish clothes", "wearing a bikini on a tropical beach")
                    base_prompt = base_prompt.replace("office blouse", "wearing a bikini on a tropical beach")
                    base_prompt = base_prompt.replace("crop top, leather jacket", "wearing a bikini on a tropical beach")
                    base_prompt = base_prompt.replace("luxury business suit, rich interior background", "wearing a bikini on a tropical beach")
                    base_prompt = base_prompt.replace("summer dress, holding a flower, sunny park background", "wearing a bikini on a tropical beach")
                    if "bikini" not in base_prompt:
                        base_prompt += ", wearing a bikini on a beautiful beach background"

                seed = random.randint(1, 999999)
                
                # Принудительно очищаем промпт от скрытых переносов строк и пробелов по краям
                clean_prompt = base_prompt.replace("\n", " ").replace("\r", " ").strip()
                
                # Безопасно кодируем чистый текст промпта для передачи в GET-запросе URL
                encoded_prompt = urllib.parse.quote(clean_prompt)
                
                # Правильный и актуальный URL эндпоинта Pollinations AI
                photo_url = f"https://pollinations.ai{encoded_prompt}?seed={seed}&width=1024&height=1024"
                
                # Логируем ссылку для отладки в терминале
                logger.info(f"Generated photo URL: {photo_url}")
                
                # Отправляем реальную фотографию в Telegram с подписью под ней
                await update.message.reply_photo(
                    photo=photo_url,
                    caption="📷 Отправляю тебе своё фото! Лови 😉"
                )
                        
            except Exception as img_err:
                logger.error(f"Ошибка генерации или отправки картинки: {img_err}")
                await update.message.reply_text("💔 Ой, камера на телефоне что-то забарахлила... Попробуй ещё раз попросить?")
                
    except Exception as e:
        logger.error(f"Общая ошибка в handle_message: {e}")
        await update.message.reply_text("💔 Ошибка, попробуй ещё раз")

# ---------------- REGISTER ----------------
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ---------------- LIFESPAN (STARTUP / SHUTDOWN) ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        me = await tg_app.bot.get_me()
        logger.info(f"✅ TOKEN OK: @{me.username}")
    except InvalidToken:
        raise RuntimeError("❌ BOT_TOKEN НЕВАЛИДЕН")
    except Exception as e:
        logger.error(f"❌ Ошибка проверки токена: {e}")
        raise

    await tg_app.initialize()
    await tg_app.start()

    if WEBHOOK_URL:
        webhook_target = f"{WEBHOOK_URL}/webhook"
        await tg_app.bot.set_webhook(
            url=webhook_target,
            secret_token=WEBHOOK_SECRET
        )
        logger.info(f"🛰️ Webhook set to: {webhook_target}")
    else:
        logger.warning("⚠️ WEBHOOK_URL не задан, бот не будет получать сообщения!")

    logger.info("🚀 BOT STARTED SUCCESSFULLY")
    yield
    await tg_app.stop()
    await tg_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook(req: Request):
    try:
        x_telegram_token = req.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if WEBHOOK_SECRET and x_telegram_token != WEBHOOK_SECRET:
            logger.warning("Unauthorized webhook request blocked")
            return {"ok": False, "error": "Unauthorized"}

        data = await req.json()
        update = Update.de_json(data, tg_app.bot)
        await tg_app.process_update(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return {"ok": True}
