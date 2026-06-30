import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Set

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ─── Configuration ─────────────────────
OWNER_ID = 6980326908
MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN")
DATA_FILE = os.getenv("DATA_FILE", "cloned_bots.json")

# ─── Logging ───────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Global Storage ─────────────────────
running_apps: Dict[str, Application] = {}
bot_usernames: Dict[str, str] = {}
active_tasks: Set[asyncio.Task] = set()


# ─── Helpers ────────────────────────────
def load_cloned_bots():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading data: {e}")
    return {}


def save_cloned_bots(bots):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(bots, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving data: {e}")


def escape_html(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


async def send_owner_log(context, message: str):
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"📊 LOG\n\n{message}",
        )
    except Exception as e:
        logger.error(f"Log send failed: {e}")


# ─── START COMMAND ─────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Contact", url="https://t.me/someattachment")]
    ]
    await update.message.reply_text(
        "CONTACT FOR BOT ACCESS = @SOMEATTACHMENT",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ─── CLONE SYSTEM CORE ──────────────────
async def start_bot_instance(token: str):
    try:
        app = Application.builder().token(token).build()

        app.add_handler(CommandHandler("start", start_command))

        await app.initialize()
        await app.start()

        me = await app.bot.get_me()
        bot_usernames[token] = me.username or "Unknown"

        asyncio.create_task(app.updater.start_polling(drop_pending_updates=True))

        running_apps[token] = app
        return app

    except Exception as e:
        logger.error(f"Failed bot: {e}")
        return None


# ─── MAIN ───────────────────────────────
async def main():
    print("Starting bot system...")

    if not MAIN_BOT_TOKEN:
        print("MAIN_BOT_TOKEN missing!")
        return

    await start_bot_instance(MAIN_BOT_TOKEN)

    while True:
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
