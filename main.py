import os
import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from ai_responses import CharacterAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHARACTERS = {
    "sophia": "👰 София",
    "elena": "💃 Елена",
    "natasha": "🔥 Наташа",
    "victoria": "👿 Виктория",
    "monica": "🎁 Моника"
}

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"char_{cid}")]
        for cid, name in CHARACTERS.items()
    ]

    await update.message.reply_text(
        "👥 Выбери персонажа:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- CALLBACK ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data.startswith("char_"):
        char_id = q.data.replace("char_", "")
        context.user_data["char"] = char_id
        context.user_data["history"] = []

        await q.edit_message_text(f"Вы выбрали {CHARACTERS[char_id]}")

# ---------------- CHAT ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "char" not in context.user_data:
        await update.message.reply_text("Сначала /start")
        return

    char_id = context.user_data["char"]
    ai = CharacterAI(char_id)

    try:
        await update.message.chat.send_action("typing")
    except:
        pass

    user_text = update.message.text

    try:
        response = ai.get_response(user_text, context.user_data.get("history", []))

        history = context.user_data.get("history", [])
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": response})
        context.user_data["history"] = history[-8:]

        await update.message.reply_text(f"{CHARACTERS[char_id]}:\n\n{response}")

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Ошибка, попробуй ещё раз")

# ---------------- MAIN ----------------
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    print("BOT RUNNING")

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
