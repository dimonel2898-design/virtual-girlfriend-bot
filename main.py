import asyncio
import logging
import os
import re
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

CHOOSING_CHARACTER, CHATTING = range(2)
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "alive", "message": "Virtual Girlfriend Bot is running!"}

async def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

CHARACTERS = {
    "sophia": {"name": "София", "age": 22, "description": "Соблазнительная блондинка", "personality": "Игривая, дерзкая", "emoji": "👰", "base_prompt": "22yo beautiful blonde girl, playful look, attractive outfit, sitting on bed"},
    "elena": {"name": "Елена", "age": 24, "description": "Страстная брюнетка", "personality": "Интеллигентная, сексуальная", "emoji": "💃", "base_prompt": "24yo beautiful brunette woman, elegant dress, sensual pose"},
    "natasha": {"name": "Наташа", "age": 20, "description": "Озорная рыжеволосая", "personality": "Веселая, раскрепощенная", "emoji": "🔥", "base_prompt": "20yo beautiful ginger hair girl, cute smile, casual look"},
    "victoria": {"name": "Виктория", "age": 25, "description": "Доминантная ведьма", "personality": "Властная, требовательная", "emoji": "👿", "base_prompt": "25yo gothic beautiful woman, dominant look, dark aesthetic"},
    "monica": {"name": "Моника (Сюрприз)", "age": 23, "description": "Сюрприз на годовщину ❤️", "personality": "Взволнованная, любящая", "emoji": "🎁", "base_prompt": "23yo gorgeous woman, beautiful lingerie, bedroom, soft candlelight"},
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["history"] = []
    disclaimer = "⚠️ <b>ВНИМАНИЕ: КОНТЕНТ 18+</b>\n\nВам есть 18 лет?"
    keyboard = [[InlineKeyboardButton("✅ Согласен", callback_data="proceed"), InlineKeyboardButton("❌ Нет", callback_data="exit")]]
    await update.message.reply_html(disclaimer, reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_CHARACTER

async def proceed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    text = "👥 <b>Выберите девушку:</b>\n\n"
    keyboard = []
    for char_id, char_data in CHARACTERS.items():
        text += f"{char_data['emoji']} <b>{char_data['name']}</b> ({char_data['age']})\n"
        keyboard.append([InlineKeyboardButton(f"{char_data['emoji']} {char_data['name']}", callback_data=f"char_{char_id}")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return CHOOSING_CHARACTER

async def exit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("До свидания! 👋")
    return -1

async def character_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    char_id = query.data.replace("char_", "")
    if char_id not in CHARACTERS: return CHOOSING_CHARACTER
    
    context.user_data["character"] = char_id
    context.user_data["history"] = []
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
        profile_text = f"{char['emoji']} <b>{char['name']}</b>\n\n🎂 Возраст: {char['age']}\n💬 Начните писать..."
        
    await query.edit_message_text(profile_text, parse_mode="HTML")
    return CHATTING

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "character" not in context.user_data:
        await update.message.reply_text("❌ Выберите персонаж через команду /start")
        return CHOOSING_CHARACTER
    
    char_id = context.user_data["character"]
    char = CHARACTERS[char_id]
    user_message = update.message.text
    
    if "history" not in context.user_data:
        context.user_data["history"] = []
        
    await update.message.chat.send_action("typing")
    
    try:
        ai = CharacterAI(char_id)
        response = ai.get_response(user_message, context.user_data["history"])
        
        image_prompt = None
        text_part = response
        
        # 1. Поиск английского промпта по регулярному выражению
        match = re.search(r'(?:\[SEND_PHOTO:\s*)?(\d{2}yo\s+[a-zA-Z\s,_\-]+)(?:\])?', response)
        
        if match:
            image_prompt = match.group(1).strip()
            text_part = response[:match.start()].strip()
        else:
            # 2. Поиск промпта, если ИИ забыл выставить квадратные скобки
            for marker in ["23yo gorgeous", "22yo beautiful", "24yo beautiful", "20yo beautiful", "25yo gothic"]:
                if marker in response:
                    text_part, remaining = response.split(marker, 1)
                    image_prompt = marker + remaining
                    break
                    
        text_part = text_part.strip()
        if not text_part:
            text_part = response

        # 3. ИСПРАВЛЕНИЕ: Безопасный триггер на отправку фото
        # Если ИИ в процессе 18+ диалога забыл написать английский тег, но речь идет об интиме — ставим базовый промпт
        trigger_words = ["фото", "покажи", "раздеться", "белье", "тело", "одежд", "смотри", "взгляни", "грудь", "сексуаль", "интим"]
        is_photo_needed = any(w in user_message.lower() for w in trigger_words) or any(w in response.lower() for w in trigger_words)
        
        if not image_prompt and is_photo_needed:
            image_prompt = char["base_prompt"]
        
        # Запись в историю памяти
        context.user_data["history"].append({"role": "user", "content": user_message})
        context.user_data["history"].append({"role": "assistant", "content": text_part})
        if len(context.user_data["history"]) > 8:
            context.user_data["history"] = context.user_data["history"][-8:]
            
        # Сначала отправляем только русский текст
        await update.message.reply_html(f"{char['emoji']} <b>{char['name']}:</b>\n\n{text_part}")
        
        # Отправляем фото только если image_prompt РЕАЛЬНО сформирован
        if image_prompt:
            await update.message.chat.send_action("upload_photo")
            image_url = ai.generate_image_url(image_prompt)
            await update.message.reply_photo(
                photo=image_url,
                caption=f"📸 Фото от {char['name']}\n\n⚙️ <i>Чтобы сменить персонажа, введи /start</i>",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Извини, у меня произошёл внутренний сбой. Напиши мне ещё раз!")
    
    return CHATTING

async def main_async() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_CHARACTER: [
                CallbackQueryHandler(proceed_callback, pattern="^proceed$"),
                CallbackQueryHandler(exit_callback, pattern="^exit$"),
                CallbackQueryHandler(character_selected, pattern="^char_"),
            ],
            CHATTING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv_handler)
    
    # 1. Пошаговая инициализация
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("🤖 Бот успешно запущен в режиме polling!")
    
    # 2. Фоновый веб-сервер
    asyncio.create_task(run_web_server())
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main_async())
