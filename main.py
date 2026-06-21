import os
import logging
import random
import urllib.parse
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
Application,
CommandHandler,
MessageHandler,
ContextTypes,
filters,
)
from telegram.error import InvalidToken

from ai_responses import CharacterAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secret")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
raise RuntimeError("BOT_TOKEN не найден")

tg_app = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
"🚀 Bot запущен"
)

async def handle_message(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):
try:

```
    char_id = context.user_data.get(
        "char",
        "sophia",
    )

    ai = CharacterAI(char_id)

    user_text = (
        update.message.text or ""
    )

    history = context.user_data.get(
        "history",
        [],
    )

    response = ai.get_response(
        user_text,
        history,
    )

    history.append(
        {
            "role": "user",
            "content": user_text,
        }
    )

    history.append(
        {
            "role": "assistant",
            "content": response,
        }
    )

    context.user_data["history"] = history[-8:]

    await update.message.reply_text(
        response
    )

    photo_triggers = [
        "фот",
        "селфи",
        "снимок",
        "покажи",
        "выгляди",
        "купальник",
    ]

    text_lower = user_text.lower()

    if any(
        x in text_lower
        for x in photo_triggers
    ):

        prompt = ai.get_image_prompt()

        if "купальник" in text_lower:
            prompt += (
                ", wearing bikini "
                "on tropical beach"
            )

        seed = random.randint(
            1,
            999999,
        )

        clean_prompt = (
            prompt
            .replace("\n", " ")
            .replace("\r", " ")
            .strip()
        )

        encoded = urllib.parse.quote(
            clean_prompt
        )

        photo_url = (
            "https://image.pollinations.ai/prompt/"
            + encoded
            + f"?seed={seed}&width=1024&height=1024"
        )

        logger.info(
            f"Generated photo URL: {photo_url}"
        )

        await update.message.reply_photo(
            photo=photo_url,
            caption="📷 Лови фото 😉",
        )

except Exception:

    logger.exception(
        "handle_message error"
    )

    await update.message.reply_text(
        "💔 Ошибка"
    )
```

tg_app.add_handler(
CommandHandler(
"start",
start,
)
)

tg_app.add_handler(
MessageHandler(
filters.TEXT
& ~filters.COMMAND,
handle_message,
)
)

@asynccontextmanager
async def lifespan(app):

```
try:

    me = await tg_app.bot.get_me()

    logger.info(
        f"TOKEN OK @{me.username}"
    )

except InvalidToken:

    raise RuntimeError(
        "Неверный BOT_TOKEN"
    )

await tg_app.initialize()

await tg_app.start()

if WEBHOOK_URL:

    await tg_app.bot.set_webhook(
        url=f"{WEBHOOK_URL}/webhook",
        secret_token=WEBHOOK_SECRET,
    )

    logger.info(
        "Webhook установлен"
    )

yield

await tg_app.stop()

await tg_app.shutdown()
```

app = FastAPI(
lifespan=lifespan
)

@app.get("/")
async def root():

```
return {
    "status": "ok"
}
```

@app.post("/webhook")
async def webhook(
req: Request
):

```
try:

    token = req.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if (
        WEBHOOK_SECRET
        and token != WEBHOOK_SECRET
    ):

        return {
            "ok": False
        }

    data = await req.json()

    update = Update.de_json(
        data,
        tg_app.bot,
    )

    await tg_app.process_update(
        update
    )

except Exception:

    logger.exception(
        "webhook error"
    )

return {
    "ok": True
}
```
