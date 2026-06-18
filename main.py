import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from ai_responses import CharacterAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secret")

app = FastAPI()

# ---------------- TELEGRAM APP ----------------
tg_app = Application.builder().token(BOT_TOKEN).build()

# ---------------- CHARACTERS ----------------
CHARACTERS = {
    "sophia": "👰 София",
    "elena": "💃 Елена",
    "natasha": "🔥 Наташа",
    "victoria": "👿 Виктория",
    "monica": "🎁 Моника"
}

# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает V3 🚀")

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

# ---------------- WEBHOOK ENDPOINT ----------------
@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, tg_app.bot)

        await tg_app.process_update(update)

    except Exception as e:
        logger.error(f"Webhook error: {e}")

    return {"ok": True}

# ---------------- SET WEBHOOK ----------------
@app.on_event("startup")
async def on_start():
    await tg_app.initialize()
    await tg_app.start()

    webhook_url = os.getenv("WEBHOOK_URL")

    if webhook_url:
        await tg_app.bot.set_webhook(
            url=f"{webhook_url}/webhook",
            secret_token=WEBHOOK_SECRET
        )

    print("🚀 V3 WEBHOOK BOT RUNNING")
