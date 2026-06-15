from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client(
    "pro_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50,
    max_concurrent_transmissions=10
)

user_files = {}
user_mode = {}

# Start with buttons
@app.on_message(filters.command("start"))
async def start(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Rename File", callback_data="rename")],
        [InlineKeyboardButton("📄 File Info", callback_data="info")]
    ])
    await message.reply("👋 Welcome to PRO BOT\nChoose an option:", reply_markup=buttons)

# Button clicks
    @app.on_callback_query()
async def callback(client, query):
    if query.data == "rename":
        user_mode[query.message.chat.id] = "rename"

        text = (
            "✏️ Rename Mode Activated\n\n"
            "📌 How to use:\n"
            "1. Send any file\n"
            "2. Then send new file name\n\n"
            "⚙️ Extra Features:\n"
            "• /setthumb → Set thumbnail\n"
            "• /delthumb → Delete thumbnail\n"
            "• /viewthumb → View thumbnail\n\n"
            "💡 Thumbnail will be added automatically!"
        )

        await query.message.reply(text)

    elif query.data == "info":
        user_mode[query.message.chat.id] = "info"
        await query.message.reply("📄 Send file to get info")
    if query.data == "rename":
        user_mode[query.message.chat.id] = "rename"
        await query.message.reply("📤 Send file to rename")

    elif query.data == "info":
        user_mode[query.message.chat.id] = "info"
        await query.message.reply("📤 Send file to get info")

# Progress function
async def progress(current, total, message, start):
    now = time.time()
    diff = now - start

    if round(diff % 1) == 0:
        percent = current * 100 / total
        await message.edit(f"📊 {percent:.2f}% completed")

# Receive file
@app.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client, message):
    mode = user_mode.get(message.chat.id)

    msg = await message.reply("📥 Downloading...")
    start = time.time()

    file_path = await message.download(progress=progress, progress_args=(msg, start))

    if mode == "rename":
        user_files[message.chat.id] = file_path
        await msg.edit("✏️ Send new file name")

    elif mode == "info":
        size = os.path.getsize(file_path) / (1024*1024)
        await msg.edit(f"📄 File Name: {os.path.basename(file_path)}\n📦 Size: {size:.2f} MB")
        os.remove(file_path)

# Rename
@app.on_message(filters.text)
async def rename(client, message):
    if message.chat.id in user_files:
        old = user_files[message.chat.id]
        new = message.text

        os.rename(old, new)

        msg = await message.reply("📤 Uploading...")
        start = time.time()

        await message.reply_document(new, progress=progress, progress_args=(msg, start))

        os.remove(new)
        del user_files[message.chat.id]

app.run()

added pro ui
