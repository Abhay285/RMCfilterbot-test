# client.py
from pyrogram import Client
from info import API_ID, API_HASH, BOT_TOKEN

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="RMCFILTERBOT",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins={"root": "plugins"}
        )


# main.py
from client import Bot

print("Bot Started 👍 Powered By @VJ_Botz")
Bot().run()
