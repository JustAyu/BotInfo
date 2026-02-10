import os, sys, time, asyncio, subprocess

# ───────────────────────
# AUTO INSTALL PACKAGES
# ───────────────────────
def ensure_package(pkg):
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--no-cache-dir", pkg]
        )

ensure_package("pyrofork")
ensure_package("aiohttp")

# ───────────────────────
# IMPORTS (AFTER INSTALL)
# ───────────────────────
from pyrogram import Client, filters
from aiohttp import web

# ───────────────────────
# ENV CONFIG
# ───────────────────────
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise RuntimeError("Missing API_ID, API_HASH or BOT_TOKEN env variables")

# ───────────────────────
# BOT INIT
# ───────────────────────
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

START_TIME = time.time()

# ───────────────────────
# HUMAN READABLE UPTIME
# ───────────────────────
def human_uptime(seconds: int) -> str:
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    out = []
    if days:
        out.append(f"{days}d")
    if hours:
        out.append(f"{hours}h")
    if minutes:
        out.append(f"{minutes}m")
    out.append(f"{seconds}s")

    return " ".join(out)

# ───────────────────────
# BOT HANDLER
# ───────────────────────
@app.on_message(filters.text & filters.private)
async def echo(_, message):
    await message.reply_text(message.text)

# ───────────────────────
# UPTIMEROBOT SERVER
# ───────────────────────
async def healthcheck(_):
    uptime = human_uptime(int(time.time() - START_TIME))
    return web.json_response({
        "status": "ok",
        "uptime": uptime
    })

async def start_web():
    web_app = web.Application()
    web_app.router.add_get("/", healthcheck)
    web_app.router.add_get("/health", healthcheck)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# ───────────────────────
# MAIN
# ───────────────────────
async def main():
    await start_web()
    await app.start()
    print("✅ Bot + Uptime server running")
    await asyncio.Event().wait()

asyncio.run(main())
