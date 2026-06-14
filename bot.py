from pyrogram import Client, filters
import os

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_files = {}

@app.on_message(filters.document | filters.video | filters.audio)
async def get_file(client, message):
    file_path = await message.download()
    user_files[message.chat.id] = file_path
    await message.reply("Send new file name")

@app.on_message(filters.text)
async def rename_file(client, message):
    if message.chat.id in user_files:
        old_file = user_files[message.chat.id]
        new_name = message.text

        os.rename(old_file, new_name)

        await message.reply_document(new_name)

        os.remove(new_name)
        del user_files[message.chat.id]

app.run()
