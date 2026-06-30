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

─── Configuration ────────────────────────────────────────────────────────────
OWNER_ID = 6980326908
MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN")
DATA_FILE = os.getenv("DATA_FILE", "cloned_bots.json")

─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(name)

─── Global Storage ───────────────────────────────────────────────────────────
running_apps: Dict[str, Application] = {}
bot_usernames: Dict[str, str] = {}
active_tasks: Set[asyncio.Task] = set()

─── Helpers ──────────────────────────────────────────────────────────────────

def load_cloned_bots() -> Dict[str, str]:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading data: {e}")
    return {}


def save_cloned_bots(bots: Dict[str, str]) -> None:
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(bots, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving data: {e}")


def escape_html(text: str) -> str:
    """HTML special chars escape karo taaki parse error na aaye."""
    return (
        text.replace("&", "&amp;")
            .replace("", "&gt;")
    )


async def send_owner_log(context: ContextTypes.DEFAULT_TYPE, message: str) -> None:
    """
    Owner ko HTML mode mein log bhejo.
    HTML use kar rahe hain taaki underscore wale usernames Markdown tod na de.
    """
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"📊 LOG\n\n{message}",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Failed to send log to owner: {e}")

─── /start ───────────────────────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    keyboard = [
        [
            InlineKeyboardButton(
                "𝐓ʜɪs 𝐁ᴏᴛ 𝐈s 𝐇ᴇʀᴇ 𝐅ᴏʀ 𝐌ᴀss 𝐑ᴇᴘᴏ#ᴛɪɴɢ",
                callback_data="noop",
            )
        ],
        [
            InlineKeyboardButton(
                "𝐈ғ 𝐘ᴏᴜ 𝐖ᴀɴᴛ 𝐁ᴏᴛ 𝐀ᴄᴄᴇss 𝐎ʀ 𝐋ᴇᴀʀɴ 𝐁ᴀɴ#ɪɴɢ...!",
                callback_data="noop",
            )
        ],
        [
            InlineKeyboardButton(
                "—› Cᴏɴᴛᴀᴄᴛ : @SOMEATTACHMENT",
                url="https://t.me/someattachment",
            )
        ],
        [
            InlineKeyboardButton("𝐂ᴏɴᴛᴀᴄᴛ 📞", url="https://t.me/someattachment"),
            InlineKeyboardButton("𝐁ᴀɴɴɪɴɢ 𝐏ʀᴏᴏғs", url="https://t.me/+IIATZD-VLpxkZDE1"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

Main message fancy font mein
    await update.message.reply_text(
        text="𝗖𝗢𝗡𝗧𝗔𝗖𝗧 𝗙𝗢𝗥 𝗕𝗢𝗧 𝗔𝗖𝗖𝗘𝗦𝗦 = @SOMEATTACHMENT",
        reply_markup=reply_markup,
    )

Owner log — HTML mode, underscore escape kiya
    uname = escape_html(f"@{user.username}") if user.username else "None"
    fname = escape_html(user.first_name)
    bot_uname = escape_html(f"@{context.bot.username}" if context.bot.username else "Unknown")

    log_message = (
        f"🆕 New Start\n"
        f"👤 User: {fname}\n"
        f"🆔 ID: {user.id}\n"
        f"📱 Username: {uname}\n"
        f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"🤖 Bot: {bot_uname}"
    )
    await send_owner_log(context, log_message)

─── /help (only owner) ───────────────────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ This command is only for the owner!")
        return

    help_text = (
        "🛠 Owner Commands\n\n"
        "▸ /start — Bot start karo\n"
        "▸ /help — Yeh menu dekho\n"
        "▸ /clone — Naya bot clone karo (token bhejo)\n"
        "▸ /rmclone — Cloned bot hatao (token bhejo)\n"
        "▸ /runningbots — Abhi chal rahe saare bots dekho\n"
    )
    await update.message.reply_text(text=help_text, parse_mode="HTML")

─── /clone ───────────────────────────────────────────────────────────────────

async def clone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ This command is only for the owner!")
        return

    await update.message.reply_text(
        text="🤖 Clone Bot\n\nPlease send the bot token:",
        parse_mode="HTML",
    )
    context.user_data["waiting_for"] = "clone_token"

─── /rmclone ─────────────────────────────────────────────────────────────────

async def rmclone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ This command is only for the owner!")
        return

    await update.message.reply_text(
        text="🗑️ Remove Clone\n\nPlease send the bot token to remove:",
        parse_mode="HTML",
    )
    context.user_data["waiting_for"] = "remove_token"

─── /runningbots ─────────────────────────────────────────────────────────────

async def runningbots_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ This command is only for the owner!")
        return

    if not running_apps:
        await update.message.reply_text("📭 No bots are currently running.")
        return

    cloned_bots = load_cloned_bots()
    lines = []
    for token in running_apps:
        username = escape_html(bot_usernames.get(token, "Unknown"))
        saved = token in cloned_bots or token == MAIN_BOT_TOKEN
        status = "✅ Active" if saved else "⚠️ Not saved"
        lines.append(f"• @{username} — {status}")

    message = "🤖 Running Bots:\n\n" + "\n".join(lines)
    await update.message.reply_text(text=message, parse_mode="HTML")

─── Noop Callback ────────────────────────────────────────────────────────────

async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Text-only buttons ka spinner band karo."""
    await update.callback_query.answer()

─── Message Handler ──────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if "waiting_for" not in context.user_data:
        return

    waiting_for = context.user_data.pop("waiting_for")
    token = update.message.text.strip()

    if waiting_for == "clone_token":
        await process_clone(update, context, token)
    elif waiting_for == "remove_token":
        await process_remove(update, context, token)

─── Clone Logic ──────────────────────────────────────────────────────────────

async def process_clone(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    try:
        if not token or ":" not in token:
            await update.message.reply_text("❌ Invalid token format!")
            return

        if token in running_apps:
            await update.message.reply_text("⚠️ This bot is already running!")
            return

        msg = await update.message.reply_text("⏳ Starting bot…")

        app = await start_bot_instance(token)
        if app:
            cloned_bots = load_cloned_bots()
            cloned_bots[token] = token
            save_cloned_bots(cloned_bots)

            username = escape_html(bot_usernames.get(token, "Unknown"))
            await msg.edit_text(
                text=f"✅ Bot Cloned Successfully!\n\n🤖 @{username}",
                parse_mode="HTML",
            )
            await send_owner_log(
                context,
                f"✅ New bot cloned: @{username}\n"
                f"🆔 Token: {escape_html(token[:20])}…",
            )
        else:
            await msg.edit_text("❌ Failed to start bot. Check the token and try again.")

    except Exception as e:
        logger.error(f"Error cloning bot: {e}")
        await update.message.reply_text(f"❌ Error: {escape_html(str(e))}", parse_mode="HTML")

─── Remove Logic ─────────────────────────────────────────────────────────────

async def process_remove(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    try:
        cloned_bots = load_cloned_bots()

        if token not in cloned_bots:
            await update.message.reply_text("❌ Bot not found in cloned list!")
            return

        if token in running_apps:
            app = running_apps[token]
            username = escape_html(bot_usernames.pop(token, "Unknown"))

            try:
                await app.updater.stop()
            except Exception:
                pass
            await app.stop()
            await app.shutdown()
            running_apps.pop(token)

            await update.message.reply_text(f"✅ Bot @{username} stopped successfully!")
        else:
            await update.message.reply_text("⚠️ Bot was not running.")

        cloned_bots.pop(token)
        save_cloned_bots(cloned_bots)
        await update.message.reply_text("🗑️ Bot removed from list!")

    except Exception as e:
        logger.error(f"Error removing bot: {e}")
        await update.message.reply_text(f"❌ Error: {escape_html(str(e))}", parse_mode="HTML")

─── Bot Instance Starter ─────────────────────────────────────────────────────

async def start_bot_instance(token: str):
    try:
        app = Application.builder().token(token).build()

Saare handlers register karo
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("clone", clone_command))
        app.add_handler(CommandHandler("rmclone", rmclone_command))
        app.add_handler(CommandHandler("runningbots", runningbots_command))
        app.add_handler(CallbackQueryHandler(noop_callback, pattern="^noop$"))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        await app.initialize()
        await app.start()

Username abhi fetch karo — baad mein None aata hai
        me = await app.bot.get_me()
        bot_usernames[token] = me.username or "Unknown"

        task = asyncio.create_task(
            app.updater.start_polling(drop_pending_updates=True)
        )
        active_tasks.add(task)
        task.add_done_callback(active_tasks.discard)

        running_apps[token] = app
        logger.info(f"Bot started: @{bot_usernames[token]}")
        return app

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        return None

─── Main ─────────────────────────────────────────────────────────────────────

async def main() -> None:
    print("🚀 Starting Telegram Clone Bot System…")

    main_app = await start_bot_instance(MAIN_BOT_TOKEN)
    if not main_app:
        print("❌ Failed to start main bot!")
        return

    print(f"✅ Main bot started: @{bot_usernames.get(MAIN_BOT_TOKEN, '?')}")

    cloned_bots = load_cloned_bots()
    if cloned_bots:
        print(f"\n🔄 Loading {len(cloned_bots)} cloned bot(s)…")
        for token in cloned_bots:
            if token == MAIN_BOT_TOKEN:
                continue
            print("  ⏳ Starting cloned bot…")
            app = await start_bot_instance(token)
            if app:
                print(f"  ✅ Started: @{bot_usernames.get(token, '?')}")
            else:
                print("  ❌ Failed to start cloned bot")
            await asyncio.sleep(0.5)

    print(f"\n✨ All bots running! Total: {len(running_apps)}")
    print("📊 Press Ctrl+C to stop all bots\n")

    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Shutting down all bots…")
        for app in list(running_apps.values()):
            try:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
            except Exception:
                pass
        print("✅ All bots stopped!")


if name == "main":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
