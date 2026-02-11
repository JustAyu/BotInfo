import os
import time
import asyncio
import logging
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid, UserIsBlocked, ChatAdminRequired
from pyrogram.enums import ChatMemberStatus

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = 7467775243
LOGGER_GROUP_ID = int(os.environ.get("LOGGER_GROUP_ID", 0))
PORT = int(os.environ.get("PORT", 10000))

# Validation
if not all([API_ID, API_HASH, BOT_TOKEN, LOGGER_GROUP_ID]):
    logger.error("Missing required environment variables!")
    raise ValueError("API_ID, API_HASH, BOT_TOKEN, and LOGGER_GROUP_ID are required")

MEMORY = []

app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    no_updates=False
)

START_TIME = time.time()

def human_uptime(seconds: int) -> str:
    """Convert seconds to human-readable uptime format"""
    try:
        d, seconds = divmod(int(seconds), 86400)
        h, seconds = divmod(seconds, 3600)
        m, s = divmod(seconds, 60)
        out = []
        if d: out.append(f"{d}d")
        if h: out.append(f"{h}h")
        if m: out.append(f"{m}m")
        out.append(f"{s}s")
        return " ".join(out)
    except Exception as e:
        logger.error(f"Error in human_uptime: {e}")
        return "N/A"

@app.on_message(filters.command("ping") & filters.user(OWNER_ID))
async def ping(_, msg: Message):
    """Ping command - only owner"""
    try:
        uptime = human_uptime(int(time.time() - START_TIME))
        await msg.reply_text(
            f"🏓 Pong!\n⏱ Uptime: `{uptime}`"
        )
    except Exception as e:
        logger.error(f"Error in ping command: {e}")
        try:
            await msg.reply_text(f"❌ Error: {str(e)[:100]}")
        except:
            pass

@app.on_message(filters.text & ~filters.command("ping") & filters.group)
async def group_handler(client, msg: Message):
    chat = msg.chat
    if chat.id in MEMORY:
        return
    link = chat.invite_link or (msg.link if msg.link else "Not Available")
    admin_info = "❌ Bot is not admin"
    try:
        me = await client.get_chat_member(chat.id, "me")
        if me.status==ChatMemberStatus.ADMINISTRATOR:
            p = me.privileges
            admin_info = (
                "✅ **Bot is Admin**\n"
                f"🏷 Title: `{me.custom_title or 'Admin'}`\n"
                f"✏️ Edit: {p.can_change_info}\n"
                f"🗑 Delete: {p.can_delete_messages}\n"
                f"📌 Pin: {p.can_pin_messages}\n"
                f"➕ Invite: {p.can_invite_users}\n"
                f"🚫 Ban: {p.can_restrict_members}\n"
                f"📣 Promote: {p.can_promote_members}")
    except Exception:
        pass
    text = (
        "👥 **GROUP MESSAGE**\n\n"
        f"📛 Group: {chat.title}\n"
        f"🆔 Chat ID: `{chat.id}`\n"
        f"🔗 Link: {link}\n\n"
        f"👤 From: {mention}\n"
        f"🆔 User ID: `{user.id}`\n\n"
        f"{admin_info}")
    try:
        await client.send_message(LOGGER_GROUP_ID, text)
        MEMORY.append(chat.id)
    except Exception as e:
        logger.error(f"Error sending group message log: {e}")
    return



@app.on_message(filters.text & ~filters.command("ping") & filters.private)
async def logger_handler(client, msg: Message):
    """Log messages from private chats and groups"""
    try:
        user = msg.from_user
        if user.id in MEMORY:
            return
        text = (
            "📩 **PRIVATE MESSAGE**\n\n"
            f"👤 Name: {user.first_name or 'N/A'}\n"
            f"🆔 ID: `{user.id}`\n"
            f"🔗 Mention: {user.mention}\n"
            f"🗯 Text: {msg.text if msg.text else 'N/A'}"
            )
        try:
            if user.photo:
                photo = await client.download_media(user.photo.big_file_id)
                if photo:
                    await client.send_photo(LOGGER_GROUP_ID, photo, caption=text)
                else:
                    await client.send_message(LOGGER_GROUP_ID, text)
            else:
                await client.send_message(LOGGER_GROUP_ID, text)
            MEMORY.append(chat.id)
        except Exception as e:
            logger.error(f"Error sending private message log: {e}")
            return
        return
    except Exception as e:
        logger.error(f"Unexpected error in logger_handler: {e}")
        return


async def healthcheck(request):
    """Health check endpoint"""
    try:
        return web.json_response({
            "status": "ok",
            "uptime": human_uptime(int(time.time() - START_TIME)),
            "bot_running": app.is_connected
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return web.json_response({
            "status": "error",
            "message": str(e)
        }, status=500)

async def start_web():
    """Start web server for health checks"""
    try:
        web_app = web.Application()
        web_app.router.add_get("/", healthcheck)
        web_app.router.add_get("/health", healthcheck)
        
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        logger.info(f"✅ Web server running on port {PORT}")
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
        raise

async def main():
    """Main function"""
    try:
        logger.info("Starting bot...")
        async with app:
            await start_web()
            logger.info("✅ Bot started successfully!")
            await idle()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    try:
        app.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
