import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import InvalidToken

from ai_responses import CharacterAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- ENV ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secret")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()

# ---------------- TOKEN CHECK ----------------
def check_token_or_crash():
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN не найден в ENV")

    try:
        bot = Bot(token=BOT_TOKEN)
        me = bot.get_me()
        logger.info(f"✅ TOKEN OK: @{me.username}")
        return bot

    except InvalidToken:
        raise RuntimeError("❌ BOT_TOKEN НЕВАЛИДЕН")

# проверка ДО старта приложения
check_token_or_crash()

# ---------------- TELEGRAM APP ----------------
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

        response = ai.get_response(user_text, history)

        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": response})
        context.user_data["history"] = history[-8:]

        await update.message.reply_text(response)

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("💔 Ошибка, попробуй ещё раз")

# ---------------- REGISTER ----------------
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ---------------- WEBHOOK ----------------
@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, tg_app.bot)
        await tg_app.process_update(update)

    except Exception as e:
        logger.error(f"Webhook error: {e}")

    return {"ok": True}

# ---------------- STARTUP ----------------
@app.on_event("startup")
async def startup():
    await tg_app.initialize()
    await tg_app.start()

    if WEBHOOK_URL:
        await tg_app.bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook",
            secret_token=WEBHOOK_SECRET
        )

    logger.info("🚀 BOT STARTED SUCCESSFULLY")
