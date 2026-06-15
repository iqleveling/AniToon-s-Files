from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("big_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_files = {}
user_mode = {}
thumbs = {}
waiting_thumb = {}
auto_rename = {}

# START
@app.on_message(filters.command("start"))
async def start(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Rename", callback_data="rename")],
        [InlineKeyboardButton("📄 File Info", callback_data="info")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ])
    await message.reply("👋 Welcome to BIG PRO BOT", reply_markup=buttons)

# BUTTONS
@app.on_callback_query()
async def callback(client, query):
    data = query.data

    if data == "rename":
        user_mode[query.message.chat.id] = "rename"
        await query.message.reply(
            "✏️ Rename Mode\n\n"
            "1. Send file\n"
            "2. Send new name\n\n"
            "Use /setthumb for thumbnail"
        )

    elif data == "info":
        user_mode[query.message.chat.id] = "info"
        await query.message.reply("📄 Send file")

    elif data == "settings":
        await query.message.reply(
            "⚙️ Settings:\n"
            "/setthumb\n"
            "/delthumb\n"
            "/autorename name.mp4\n"
            "/cancel"
        )

    elif data == "help":
        await query.message.reply(
            "❓ Help:\n\n"
            "Rename → send file → send name\n"
            "Info → send file\n"
            "Thumbnail → /setthumb\n"
            "Cancel → /cancel"
        )

# PROGRESS
async def progress(current, total, message, start):
    percent = current * 100 / total
    await message.edit(f"📊 {percent:.1f}%")

# FILE RECEIVE
@app.on_message(filters.document | filters.video | filters.audio)
async def file_handler(client, message):
    mode = user_mode.get(message.chat.id)

    msg = await message.reply("📥 Downloading...")
    file_path = await message.download()

    if mode == "rename":
        user_files[message.chat.id] = file_path
        await msg.edit("✏️ Send new file name")

    elif mode == "info":
        size = os.path.getsize(file_path) / (1024*1024)
        await msg.edit(
            f"📄 Name: {os.path.basename(file_path)}\n"
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

        await message.reply("📤 Uploading...")
        await message.reply_document(new, thumb=thumbs.get(message.chat.id))

        os.remove(new)
        del user_files[message.chat.id]

# AUTO RENAME
@app.on_message(filters.command("autorename"))
async def auto(client, message):
    text = message.text.split(" ", 1)

    if len(text) < 2:
        return await message.reply("Usage: /autorename name.mp4")

    auto_rename[message.chat.id] = text[1]
    await message.reply(f"✅ Auto rename set: {text[1]}")

# CANCEL
@app.on_message(filters.command("cancel"))
async def cancel(client, message):
    user_files.pop(message.chat.id, None)
    user_mode.pop(message.chat.id, None)
    await message.reply("❌ Process cancelled")

# THUMBNAIL
@app.on_message(filters.command("setthumb"))
async def ask_thumb(client, message):
    waiting_thumb[message.chat.id] = True
    await message.reply("📸 Send photo")

@app.on_message(filters.photo)
async def save_thumb(client, message):
    if waiting_thumb.get(message.chat.id):
        file = await message.download()
        thumbs[message.chat.id] = file
        waiting_thumb.pop(message.chat.id)
        await message.reply("✅ Thumbnail saved")

@app.on_message(filters.command("delthumb"))
async def del_thumb(client, message):
    if message.chat.id in thumbs:
        os.remove(thumbs[message.chat.id])
        del thumbs[message.chat.id]
        await message.reply("❌ Thumbnail deleted")
    else:
        await message.reply("No thumbnail")

# VIEW THUMB
@app.on_message(filters.command("viewthumb"))
async def view_thumb(client, message):
    if message.chat.id in thumbs:
        await message.reply_photo(thumbs[message.chat.id])
    else:
        await message.reply("No thumbnail")

app.run()
