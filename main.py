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

        # Список триггеров для отправки сгенерированных фотографий
        photo_triggers = ["фото", "фотку", "фотографию", "покажи себя", "как выглядишь", "своё фото", "селфи", "снимок"]
        user_text_lower = user_text.lower()

        # Проверяем, содержит ли текст пользователя запрос на фото
        if any(trigger in user_text_lower for trigger in photo_triggers):
            # 1. Сначала отправляем кокетливый текстовый ответ ИИ
            await update.message.reply_text(response)
            
            # 2. Включаем анимацию "отправка фото" в интерфейсе Telegram
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
            
            # 3. Извлекаем описание внешности (промпт) из ai_responses.py
            # Если метода get_image_prompt нет, используем дефолтный базовый промпт
            if hasattr(ai, "get_image_prompt"):
                base_prompt = ai.get_image_prompt()
            else:
                base_prompt = "A beautiful 22-year-old playful girl, cute smile, blonde hair, photorealistic, 4k"
            
            # Генерируем уникальный seed, чтобы фотографии каждый раз отличались ракурсом и одеждой
            seed = random.randint(1, 999999)
            encoded_prompt = urllib.parse.quote(base_prompt)
            
            # Формируем прямую ссылку на бесплатный генератор изображений Pollinations (модель Flux)
            photo_url = f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&seed={seed}&model=flux"
            
            # 4. Отправляем пользователю реальное изображение
            await update.message.reply_photo(
                photo=photo_url,
                caption="📸 Лови моё фото! Как тебе? 😉"
            )
        else:
            # Если пользователь фото не просил — просто присылаем обычный текст
            await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
        await update.message.reply_text("💔 Ошибка, попробуй ещё раз")

# ---------------- REGISTER ----------------
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ---------------- LIFESPAN (STARTUP / SHUTDOWN) ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Проверка токена ---
    try:
        me = await tg_app.bot.get_me()
        logger.info(f"✅ TOKEN OK: @{me.username}")
    except InvalidToken:
        raise RuntimeError("❌ BOT_TOKEN НЕВАЛИДЕН")
    except Exception as e:
        logger.error(f"❌ Ошибка проверки токена: {e}")
        raise

    # --- Инициализация бота ---
    await tg_app.initialize()
    await tg_app.start()

    # --- Установка Вебхука ---
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
    
    # --- Корректное отключение при остановке сервера ---
    await tg_app.stop()
    await tg_app.shutdown()

# Инициализируем FastAPI с менеджером жизненного цикла приложений
app = FastAPI(lifespan=lifespan)

# ---------------- WEBHOOK ENDPOINT ----------------
@app.post("/webhook")
async def webhook(req: Request):
    try:
        # Проверяем секретный токен от Telegram для безопасности
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
