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
)
from ai_responses import CharacterAI

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["history"] = []
    context.user_data["character"] = None
    
    disclaimer = (
        "⚠️ <b>ВНИМАНИЕ: КОНТЕНТ 18+</b>\n\n"
        "Вам есть 18 лет?\n\n"
        "🤖 Бот использует Groq AI (LLaMA 3.3)\n"
        "⚡ Бесплатный • Без ограничений • Без цензуры"
    )
    keyboard = [[InlineKeyboardButton("✅ Согласен", callback_data="proceed"), InlineKeyboardButton("❌ Нет", callback_data="exit")]]
    
    if update.message:
        await update.message.reply_html(disclaimer, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_html(disclaimer, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "exit":
        await query.edit_message_text("До свидания! 👋")
        return

    if data == "proceed" or data == "back":
        context.user_data["character"] = None
        context.user_data["history"] = []
        text = "👥 <b>Выберите девушку для общения:</b>\n\n"
        keyboard = []
        for char_id, char_data in CHARACTERS.items():
            text += f"{char_data['emoji']} <b>{char_data['name']}</b> ({char_data['age']})\n"
            keyboard.append([InlineKeyboardButton(f"{char_data['emoji']} {char_data['name']}", callback_data=f"char_{char_id}")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    if data.startswith("char_"):
        char_id = data.replace("char_", "")
        if char_id not in CHARACTERS:
            return
        
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
                f"💬 <b>Ответьте Монике прямо в чат, чтобы начать сценарий...</b>"
            )
        else:
            profile_text = f"{char['emoji']} <b>{char['name']}</b>\n\n🎂 Возраст: {char['age']}\n💬 Начните писать ей прямо в чат..."
            
        await query.message.reply_html(profile_text)
        try:
            await query.message.delete()
        except Exception:
            pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if "character" not in context.user_data or not context.user_data["character"]:
        await update.message.reply_text("❌ Пожалуйста, сначала выберите персонажа кнопкой или введите команду /start")
        return
    
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
        
        start_idx = response.find("[SEND_PHOTO:")
        if start_idx != -1:
            text_part = response[:start_idx].strip()
            end_idx = response.find("]", start_idx)
            if end_idx != -1:
                image_prompt = response[start_idx + 12:end_idx].strip()
            else:
                image_prompt = response[start_idx + 12:].strip()
        else:
            for marker in ["23yo gorgeous", "22yo beautiful", "24yo beautiful", "20yo beautiful", "25yo gothic"]:
                if marker in response:
                    m_idx = response.find(marker)
                    text_part = response[:m_idx].strip()
                    image_prompt = response[m_idx:].strip()
                    break
        
        text_part = text_part.strip()
        if not text_part:
            text_part = response
            
        trigger_words = ["фото", "покажи", "раздеться", "белье", "тело", "одежд", "смотри", "взгляни", "грудь", "сексуаль", "интим"]
        is_photo_requested = any(w in user_message.lower() for w in trigger_words) or any(w in response.lower() for w in trigger_words)
        
        if not image_prompt and is_photo_requested:
            image_prompt = char["base_prompt"]
            
        context.user_data["history"].append({"role": "user", "content": user_message})
        context.user_data["history"].append({"role": "assistant", "content": text_part})
        if len(context.user_data["history"]) > 8:
            context.user_data["history"] = context.user_data["history"][-8:]
            
        await update.message.reply_html(f"{char['emoji']} <b>{char['name']}:</b>\n\n{text_part}")
        
        if image_prompt:
            await update.message.chat.send_action("upload_photo")
            image_url = ai.generate_image_url(image_prompt)
            await update.message.reply_photo(
                photo=image_url,
                caption=f"📸 Фото от {char['name']}\n\n⚙️ <i>Чтобы сменить персонажа, введи /start</i>",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text("✨ (Я попыталась отправить тебе фото, но сеть немного лагает... Напиши мне что-нибудь еще!)")

async def main_async() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("🤖 Бот успешно запущен без багов ConversationHandler!")
    
    asyncio.create_task(run_web_server())
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main_async())
