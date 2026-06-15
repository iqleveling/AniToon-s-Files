from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("ultimate_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_queue = {}
user_mode = {}
thumbs = {}
waiting_thumb = {}
auto_rename = {}

# MENU
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Rename", callback_data="rename"),
         InlineKeyboardButton("📄 Info", callback_data="info")],
        [InlineKeyboardButton("🖼️ Thumbnail", callback_data="thumb"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📂 Queue", callback_data="queue"),
         InlineKeyboardButton("❓ Help", callback_data="help")]
    ])

# START
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🚀 ULTIMATE BOT", reply_markup=menu())

# BUTTONS
@app.on_callback_query()
async def cb(client, query):
    uid = query.message.chat.id
    data = query.data

    if data == "rename":
        user_mode[uid] = "rename"
        user_queue[uid] = []
        await query.message.reply("Send multiple files")

    elif data == "info":
        user_mode[uid] = "info"
        await query.message.reply("Send file")

    elif data == "thumb":
        await query.message.reply(
            "Thumbnail",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📸 Set", callback_data="setthumb")],
                [InlineKeyboardButton("👁 View", callback_data="viewthumb")],
                [InlineKeyboardButton("❌ Delete", callback_data="delthumb")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

    elif data == "setthumb":
        waiting_thumb[uid] = True
        await query.message.reply("Send photo")

    elif data == "viewthumb":
        if uid in thumbs:
            await query.message.reply_photo(thumbs[uid])
        else:
            await query.message.reply("No thumbnail")

    elif data == "delthumb":
        if uid in thumbs:
            os.remove(thumbs[uid])
            del thumbs[uid]
            await query.message.reply("Deleted")
        else:
            await query.message.reply("No thumbnail")

    elif data == "settings":
        await query.message.reply(
            "Settings",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 Auto Rename", callback_data="autorename")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

    elif data == "autorename":
        await query.message.reply("Send base name (example: movie)")

    elif data == "queue":
        q = user_queue.get(uid, [])
        await query.message.reply(f"Files in queue: {len(q)}")

    elif data == "cancel":
        user_queue.pop(uid, None)
        user_mode.pop(uid, None)
        await query.message.reply("Cancelled")

    elif data == "help":
        await query.message.reply(
            "Rename → send many files → send name\n"
            "Auto rename adds numbers\n"
            "All features via buttons"
        )

    elif data == "back":
        await query.message.reply("Menu", reply_markup=menu())

# PROGRESS
async def progress(current, total, message, start):
    percent = current * 100 / total
    try:
        await message.edit(f"{percent:.1f}%")
    except:
        pass

# FILE HANDLER
@app.on_message(filters.document | filters.video | filters.audio)
async def files(client, message):
    uid = message.chat.id
    mode = user_mode.get(uid)

    msg = await message.reply("Downloading...")
    start = time.time()

    path = await message.download(progress=progress, progress_args=(msg, start))

    if mode == "rename":
        user_queue.setdefault(uid, []).append(path)
        await msg.edit(f"Added ({len(user_queue[uid])})\nSend name")

    elif mode == "info":
        size = os.path.getsize(path)/(1024*1024)
        await msg.edit(f"{os.path.basename(path)}\n{size:.2f} MB")
        os.remove(path)

# SAVE THUMB
@app.on_message(filters.photo)
async def thumb_save(client, message):
    uid = message.chat.id
    if waiting_thumb.get(uid):
        file = await message.download()
        thumbs[uid] = file
        waiting_thumb.pop(uid)
        await message.reply("Thumbnail saved")

# PROCESS QUEUE
@app.on_message(filters.text)
async def process(client, message):
    uid = message.chat.id

    # SET AUTO NAME
    if uid not in user_queue:
        auto_rename[uid] = message.text
        return await message.reply(f"Auto rename set: {message.text}")

    queue = user_queue.get(uid, [])

    if queue:
        base = auto_rename.get(uid, message.text)

        count = 1
        for file_path in queue:
            ext = os.path.splitext(file_path)[1]
            new_name = f"{base}_{count}{ext}"

            os.rename(file_path, new_name)

            msg = await message.reply("Uploading...")
            start = time.time()

            await message.reply_document(
                new_name,
                thumb=thumbs.get(uid),
                progress=progress,
                progress_args=(msg, start)
            )

            os.remove(new_name)
            count += 1

        user_queue[uid] = []
        await message.reply("All files done")

app.run()
