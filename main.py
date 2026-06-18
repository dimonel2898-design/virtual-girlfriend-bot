import asyncio
import logging
import os
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
from ai_responses import CharacterAI

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

CHOOSING_CHARACTER, CHATTING = range(2)

# Берем токен строго из переменных окружения Render
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настройка веб-сервера для Render
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "alive", "message": "Virtual Girlfriend Bot is running!"}

async def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

# Список персонажей бота
CHARACTERS = {
    "sophia": {
        "name": "София",
        "age": 22,
        "description": "Соблазнительная блондинка",
        "personality": "Игривая, дерзкая",
        "emoji": "👰",
    },
    "elena": {
        "name": "Елена",
        "age": 24,
        "description": "Страстная брюнетка",
        "personality": "Интеллигентная, сексуальная",
        "emoji": "💃",
    },
    "natasha": {
        "name": "Наташа",
        "age": 20,
        "description": "Озорная рыжеволосая",
        "personality": "Веселая, раскрепощенная",
        "emoji": "🔥",
    },
    "victoria": {
        "name": "Виктория",
        "age": 25,
        "description": "Доминантная ведьма",
        "personality": "Властная, требовательная",
        "emoji": "👿",
    },
    "monica": {
        "name": "Моника (Сюрприз)",
        "age": 23,
        "description": "Сюрприз на годовщину ❤️",
        "personality": "Взволнованная, любящая, романтичная",
        "emoji": "🎁",
    },
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    disclaimer = (
        "⚠️ <b>ВНИМАНИЕ: КОНТЕНТ 18+</b>\n\n"
        "Вам есть 18 лет?\n\n"
        "🤖 Бот использует Groq AI (LLaMA 3.3)\n"
        "⚡ Бесплатный • Без ограничений • Без цензуры"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Согласен", callback_data="proceed"),
         InlineKeyboardButton("❌ Нет", callback_data="exit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_html(disclaimer, reply_markup=reply_markup)
    return CHOOSING_CHARACTER

async def proceed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    text = "👥 <b>Выберите девушку:</b>\n\n"
    keyboard = []
    for char_id, char_data in CHARACTERS.items():
        text += f"{char_data['emoji']} <b>{char_data['name']}</b> ({char_data['age']})\n"
        keyboard.append([InlineKeyboardButton(
            f"{char_data['emoji']} {char_data['name']}",
            callback_data=f"char_{char_id}"
        )])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
    return CHOOSING_CHARACTER

async def exit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("До свидания! 👋")
    return -1

async def character_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    char_id = query.data.replace("char_", "")
    
    if char_id not in CHARACTERS:
        return CHOOSING_CHARACTER
    
    context.user_data["character"] = char_id
    char = CHARACTERS[char_id]
    
    if char_id == "monica":
        profile_text = (
            f"🎁 <b>{char['name']}</b>\n\n"
            f"Вы приходите домой — вокруг горят свечи, на столе стоит Ваше любимое блюдо, "
            f"а на двери в спальню висит записка: <i>«закройте глаза»</i>.\n\n"
            f"Голос Моники доносится из глубины комнаты. Она звучит взволнованно и чуть нервно:\n"
            f"«О боже, я так нервничаю! Но ты выглядишь потрясающе, правда. Я подготовила небольшой сюрприз для нашей годовщины...»\n\n"
            f"💬 <b>Ответьте Монике, чтобы начать сценарий...</b>"
        )
    else:
        profile_text = (
            f"{char['emoji']} <b>{char['name']}</b>\n\n"
            f"🎂 Возраст: {char['age']}\n"
            f"💬 Начните писать..."
        )
        
    keyboard = [[InlineKeyboardButton("🔄 Другая", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(profile_text, reply_markup=reply_markup, parse_mode="HTML")
    return CHATTING

async def back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("character", None)
    text = "👥 <b>Выберите девушку:</b>\n\n"
    keyboard = []
    for char_id, char_data in CHARACTERS.items():
        keyboard.append([InlineKeyboardButton(
            f"{char_data['emoji']} {char_data['name']}",
            callback_data=f"char_{char_id}"
        )])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
    return CHOOSING_CHARACTER

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "character" not in context.user_data:
        await update.message.reply_text("❌ Выберите персонаж /start")
        return CHOOSING_CHARACTER
    
    char_id = context.user_data["character"]
    char = CHARACTERS[char_id]
    user_message = update.message.text
    
    await update.message.chat.send_action("typing")
    
    try:
        ai = CharacterAI(char_id)
        response = ai.get_response(user_message)
        
        if "[SEND_PHOTO:" in response:
            text_part, photo_part = response.split("[SEND_PHOTO:", 1)
            image_prompt = photo_part.replace("]", "").strip()
            text_part = text_part.strip()
            
            if text_part:
                full_response = f"{char['emoji']} <b>{char['name']}:</b>\n\n{text_part}"
                await update.message.reply_html(full_response)
                
            await update.message.chat.send_action("upload_photo")
            image_url = ai.generate_image_url(image_prompt)
            
            keyboard = [[InlineKeyboardButton("🔄 Другая", callback_data="back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_photo(
                photo=image_url,
                caption=f"📸 Фото от {char['name']}",
                reply_markup=reply_markup
            )
        else:
            full_response = f"{char['emoji']} <b>{char['name']}:</b>\n\n{response}"
            keyboard = [[InlineKeyboardButton("🔄 Другая", callback_data="back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_html(full_response, reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error in conversation: {e}")
        await update.message.reply_text("❌ Ошибка ИИ. Попробуйте позже.")
    
    return CHATTING

async def run_bot(application: Application):
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("🤖 Бот успешно запущен в режиме polling!")
    
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

async def main_async() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_CHARACTER: [
                CallbackQueryHandler(proceed_callback, pattern="^proceed$"),
                CallbackQueryHandler(exit_callback, pattern="^exit$"),
                CallbackQueryHandler(character_selected, pattern="^char_"),
                CallbackQueryHandler(back_callback, pattern="^back$"),
            ],
            CHATTING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
                CallbackQueryHandler(back_callback, pattern="^back$"),
            ],
        },
        fallbacks=[],
    )
    
    application.add_handler(conv_handler)
    
    await asyncio.gather(
        run_web_server(),
        run_bot(application)
    )

if __name__ == '__main__':
    try:
        asyncio.run(main_async())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
