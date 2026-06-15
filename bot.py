from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
import subprocess
from PIL import Image

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
thumbs = {}
waiting_thumb = {}
auto_rename = {}

# START
@app.on_message(filters.command("start"))
async def start(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Rename File", callback_data="rename")],
        [InlineKeyboardButton("📄 File Info", callback_data="info")]
    ])
    await message.reply(
        "👋 Welcome to PRO BOT\nChoose an option:",
        reply_markup=buttons
    )

# BUTTONS
@app.on_callback_query()
async def callback(client, query):
    if query.data == "rename":
        user_mode[query.message.chat.id] = "rename"

        await query.message.reply(
            "✏️ Rename Mode Activated\n\n"
            "📌 Steps:\n"
            "1️⃣ Send a file 📄\n"
            "2️⃣ Wait for download ⏳\n"
            "3️⃣ Send new file name ✏️\n\n"
            "🖼️ Thumbnail Guide:\n"
            "👉 Send /setthumb\n"
            "👉 Then send a photo\n\n"
            "⚙️ Commands:\n"
            "/setthumb - Set thumbnail\n"
            "/viewthumb - View thumbnail\n"
            "/delthumb - Delete thumbnail\n"
            "/autorename name.mp4\n"
            "/toaudio (reply to video)\n"
            "/topdf (reply to image)"
        )

    elif query.data == "info":
        user_mode[query.message.chat.id] = "info"
        await query.message.reply("📄 Send file to get info")

# PROGRESS
async def progress(current, total, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 1) == 0:
        percent = current * 100 / total
        await message.edit(f"📊 {percent:.2f}% completed")

# RECEIVE FILE
@app.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client, message):
    mode = user_mode.get(message.chat.id)

    msg = await message.reply("📥 Downloading...")
    start = time.time()

    file_path = await message.download(
        progress=progress,
        progress_args=(msg, start)
    )

    if mode == "rename":
        user_files[message.chat.id] = file_path
        await msg.edit("✏️ Send new file name")

    elif mode == "info":
        size = os.path.getsize(file_path) / (1024 * 1024)
        await msg.edit(
            f"📄 File: {os.path.basename(file_path)}\n"
            f"📦 Size: {size:.2f} MB"
        )
        os.remove(file_path)

# RENAME
@app.on_message(filters.text)
async def rename(client, message):
    if message.chat.id in user_files:
        old = user_files[message.chat.id]
        new = auto_rename.get(message.chat.id, message.text)

        os.rename(old, new)

        msg = await message.reply("📤 Uploading...")
        start = time.time()

        await message.reply_document(
            new,
            thumb=thumbs.get(message.chat.id),
            progress=progress,
            progress_args=(msg, start)
        )

        os.remove(new)
        del user_files[message.chat.id]

# SET THUMB
@app.on_message(filters.command("setthumb"))
async def ask_thumb(client, message):
    waiting_thumb[message.chat.id] = True
    await message.reply("📸 Send a photo to set as thumbnail")

# SAVE THUMB
@app.on_message(filters.photo)
async def save_thumb(client, message):
    if waiting_thumb.get(message.chat.id):
        file = await message.download()
        thumbs[message.chat.id] = file
        waiting_thumb.pop(message.chat.id)

        await message.reply(
            "✅ Thumbnail saved!\nNow send file and rename"
        )

# DELETE THUMB
@app.on_message(filters.command("delthumb"))
async def del_thumb(client, message):
    if message.chat.id in thumbs:
        os.remove(thumbs[message.chat.id])
        del thumbs[message.chat.id]
        await message.reply("❌ Thumbnail deleted")
    else:
        await message.reply("No thumbnail found")

# VIEW THUMB
@app.on_message(filters.command("viewthumb"))
async def view_thumb(client, message):
    if message.chat.id in thumbs:
        await message.reply_photo(thumbs[message.chat.id])
    else:
        await message.reply("No thumbnail set")

# AUTO RENAME
@app.on_message(filters.command("autorename"))
async def set_auto(client, message):
    text = message.text.split(" ", 1)

    if len(text) < 2:
        return await message.reply("Usage:\n/autorename filename.mp4")

    auto_rename[message.chat.id] = text[1]
    await message.reply(f"✅ Auto rename set: {text[1]}")

# VIDEO → AUDIO
@app.on_message(filters.command("toaudio") & filters.reply)
async def video_to_audio(client, message):
    msg = await message.reply("🎵 Converting...")

    file = await message.reply_to_message.download()
    output = file + ".mp3"

    subprocess.call(f"ffmpeg -i '{file}' '{output}' -y", shell=True)

    await message.reply_audio(output)

    os.remove(file)
    os.remove(output)
    await msg.delete()

# IMAGE → PDF
@app.on_message(filters.command("topdf") & filters.reply)
async def image_to_pdf(client, message):
    msg = await message.reply("📄 Creating PDF...")

    file = await message.reply_to_message.download()
    image = Image.open(file).convert("RGB")

    pdf_path = file + ".pdf"
    image.save(pdf_path)

    await message.reply_document(pdf_path)

    os.remove(file)
    os.remove(pdf_path)
    await msg.delete()

app.run()
