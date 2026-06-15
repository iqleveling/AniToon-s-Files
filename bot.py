from pyrogram import Client, filters
import os
import time

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client(
    "fast_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50,
    max_concurrent_transmissions=10
)

user_files = {}

# Progress function
async def progress(current, total, message, start_time):
    now = time.time()
    diff = now - start_time

    if round(diff % 1) == 0:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        await message.edit(
            f"📊 Progress: {percentage:.2f}%\n"
            f"⚡ Speed: {speed/1024/1024:.2f} MB/s\n"
            f"📦 Done: {current/1024/1024:.2f} MB / {total/1024/1024:.2f} MB"
        )

# Start
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🚀 Send file to rename (Fast Mode Enabled)")

# Receive file
@app.on_message(filters.document | filters.video | filters.audio)
async def get_file(client, message):
    msg = await message.reply("📥 Downloading...")

    start = time.time()
    file_path = await message.download(
        progress=progress,
        progress_args=(msg, start)
    )

    user_files[message.chat.id] = file_path
    await msg.edit("✏️ Send new file name")

# Rename
@app.on_message(filters.text)
async def rename_file(client, message):
    if message.chat.id in user_files:
        old_file = user_files[message.chat.id]
        new_name = message.text

        os.rename(old_file, new_name)

        msg = await message.reply("📤 Uploading...")

        start = time.time()
        await message.reply_document(
            new_name,
            progress=progress,
            progress_args=(msg, start)
        )

        os.remove(new_name)
        del user_files[message.chat.id]

app.run()
