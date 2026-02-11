import os
import time
import asyncio
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import Message

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = 7467775243
LOGGER_GROUP_ID = int(os.environ["LOGGER_GROUP_ID"])
PORT = int(os.environ.get("PORT", 10000))

MEMORY = []

app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

START_TIME = time.time()

def human_uptime(seconds: int) -> str:
    d, seconds = divmod(seconds, 86400)
    h, seconds = divmod(seconds, 3600)
    m, s = divmod(seconds, 60)
    out = []
    if d: out.append(f"{d}d")
    if h: out.append(f"{h}h")
    if m: out.append(f"{m}m")
    out.append(f"{s}s")
    return " ".join(out)

@app.on_message(filters.command("ping") & filters.user(OWNER_ID))
async def ping(_, msg: Message):
    await msg.reply_text(
        f"🏓 Pong!\n⏱ Uptime: `{human_uptime(int(time.time() - START_TIME))}`"
    )

@app.on_message(filters.text & ~filters.command("ping"))
async def logger(client, msg: Message):
    if not msg.from_user:
        return

    user = msg.from_user
    mention = user.mention(user.id)

    if msg.chat.type == "private":

        if user.id in MEMORY:
            return

        text = (
            "📩 **PRIVATE MESSAGE**\n\n"
            f"👤 Name: {user.first_name or 'N/A'}\n"
            f"🆔 ID: `{user.id}`\n"
            f"🔗 Mention: {mention}\n"
            f"🗯 Text: {msg.text}"
        )

        if user.photo:
            photo = await client.download_media(user.photo.big_file_id)
            await client.send_photo(LOGGER_GROUP_ID, photo, caption=text)
        else:
            await client.send_message(LOGGER_GROUP_ID, text)

        MEMORY.append(user.id)
        return

    chat = msg.chat

    if chat.id in MEMORY:
        return

    link = chat.invite_link or (msg.link if msg.link else "Not Available")
    admin_info = "❌ Bot is not admin"

    try:
        me = await client.get_chat_member(chat.id, "me")

        if me.status in ("administrator", "creator"):
            p = me.privileges

            admin_info = (
                "✅ **Bot is Admin**\n"
                f"🏷 Title: `{me.custom_title or 'Admin'}`\n"
                f"✏️ Edit: {p.can_change_info}\n"
                f"🗑 Delete: {p.can_delete_messages}\n"
                f"📌 Pin: {p.can_pin_messages}\n"
                f"➕ Invite: {p.can_invite_users}\n"
                f"🚫 Ban: {p.can_restrict_members}\n"
                f"📣 Promote: {p.can_promote_members}"
            )
    except:
        pass

    text = (
        "👥 **GROUP MESSAGE**\n\n"
        f"📛 Group: {chat.title}\n"
        f"🆔 Chat ID: `{chat.id}`\n"
        f"🔗 Link: {link}\n\n"
        f"👤 From: {mention}\n"
        f"🆔 User ID: `{user.id}`\n\n"
        f"{admin_info}"
    )

    await client.send_message(LOGGER_GROUP_ID, text)
    MEMORY.append(chat.id)

async def healthcheck(_):
    return web.json_response({
        "status": "ok",
        "uptime": human_uptime(int(time.time() - START_TIME))
    })

async def start_web():
    web_app = web.Application()
    web_app.router.add_get("/", healthcheck)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main():
    await start_web()

if __name__ == "__main__":
    asyncio.run(main())
    app.run()
