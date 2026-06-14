from pyrogram import Client, filters
import os

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client(
    "rename_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.document | filters.video | filters.audio)
async def rename(client, message):
    msg = await message.reply("Downloading...")

    file_path = await message.download()

    await msg.edit("Send new name")

    new_name_msg = await client.listen(message.chat.id)
    new_name = new_name_msg.text

    os.rename(file_path, new_name)

    await msg.edit("Uploading...")

    await message.reply_document(new_name)

    os.remove(new_name)

app.run()
