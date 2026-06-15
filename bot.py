from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("ultra_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_files = {}
user_mode = {}
thumbs = {}
waiting_thumb = {}
auto_rename = {}

# MAIN MENU
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Rename", callback_data="rename"),
         InlineKeyboardButton("📄 Info", callback_data="info")],
        [InlineKeyboardButton("🖼️ Thumbnail", callback_data="thumb"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ])

# START
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🔥 ULTRA BOT\nChoose option:", reply_markup=main_menu())

# BUTTON HANDLER
@app.on_callback_query()
async def callback(client, query):
    uid = query.message.chat.id
    data = query.data

    # RENAME
    if data == "rename":
        user_mode[uid] = "rename"
        await query.message.reply(
            "✏️ Rename Mode\n\nSend file → then send new name",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )

    # INFO
    elif data == "info":
        user_mode[uid] = "info"
        await query.message.reply(
            "📄 Send file to get info",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )

    # THUMB MENU
    elif data == "thumb":
        await query.message.reply(
            "🖼️ Thumbnail Settings",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📸 Set Thumbnail", callback_data="setthumb")],
                [InlineKeyboardButton("👁 View Thumbnail", callback_data="viewthumb")],
                [InlineKeyboardButton("❌ Delete Thumbnail", callback_data="delthumb")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

    # SET THUMB
    elif data == "setthumb":
        waiting_thumb[uid] = True
        await query.message.reply("📸 Send a photo now")

    # VIEW THUMB
    elif data == "viewthumb":
        if uid in thumbs:
            await query.message.reply_photo(thumbs[uid])
        else:
            await query.message.reply("No thumbnail set")

    # DELETE THUMB
    elif data == "delthumb":
        if uid in thumbs:
            os.remove(thumbs[uid])
            del thumbs[uid]
            await query.message.reply("❌ Thumbnail deleted")
        else:
            await query.message.reply("No thumbnail")

    # SETTINGS
    elif data == "settings":
        await query.message.reply(
            "⚙️ Settings",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 Auto Rename", callback_data="autorename")],
                [InlineKeyboardButton("❌ Cancel Process", callback_data="cancel")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

    # AUTO RENAME BUTTON
    elif data == "autorename":
        await query.message.reply("Send name for auto rename")

    # CANCEL
    elif data == "cancel":
        user_files.pop(uid, None)
        user_mode.pop(uid, None)
        await query.message.reply("❌ Cancelled")

    # HELP
    elif data == "help":
        await query.message.reply(
            "❓ Help:\n\nRename → Send file → Send name\nThumbnail → Use buttons\nNo commands needed"
        )

    # BACK
    elif data == "back":
        await query.message.reply("🏠 Main Menu", reply_markup=main_menu())

# PROGRESS
async def progress(current, total, message, start):
    percent = current * 100 / total
    try:
        await message.edit(f"📊 {percent:.1f}%")
    except:
        pass

# FILE HANDLER
@app.on_message(filters.document | filters.video | filters.audio)
async def file_handler(client, message):
    uid = message.chat.id
    mode = user_mode.get(uid)

    msg = await message.reply("📥 Downloading...")
    start = time.time()

    file_path = await message.download(progress=progress, progress_args=(msg, start))

    if mode == "rename":
        user_files[uid] = file_path
        await msg.edit("✏️ Send new file name")

    elif mode == "info":
        size = os.path.getsize(file_path) / (1024 * 1024)
        await msg.edit(f"📄 {os.path.basename(file_path)}\n📦 {size:.2f} MB")
        os.remove(file_path)

# SAVE THUMB (FIXED)
@app.on_message(filters.photo)
async def save_thumb(client, message):
    uid = message.chat.id
    if waiting_thumb.get(uid):
        file = await message.download()
        thumbs[uid] = file
        waiting_thumb.pop(uid)
        await message.reply("✅ Thumbnail saved successfully!")

# TEXT HANDLER (Rename + Auto Rename)
@app.on_message(filters.text)
async def text_handler(client, message):
    uid = message.chat.id

    # AUTO RENAME SET
    if "auto rename" in message.text.lower():
        return

    # IF WAITING FILE RENAME
    if uid in user_files:
        old = user_files[uid]
        new = auto_rename.get(uid, message.text)

        os.rename(old, new)

        msg = await message.reply("📤 Uploading...")
        start = time.time()

        await message.reply_document(
            new,
            thumb=thumbs.get(uid),
            progress=progress,
            progress_args=(msg, start)
        )

        os.remove(new)
        del user_files[uid]

    else:
        # AUTO RENAME SET
        auto_rename[uid] = message.text
        await message.reply(f"✅ Auto rename set: {message.text}")

app.run()
