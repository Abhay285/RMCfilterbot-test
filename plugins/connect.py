# plugins/connect.py
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from info import DATABASE_URI

client_db = MongoClient(DATABASE_URI)
db = client_db['filterbot']
connections = db['connections']

@Client.on_message(filters.command("connect") & filters.private)
async def connect_handler(client, message: Message):
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a message in the group to connect.")
    group_id = message.reply_to_message.chat.id
    user_id = message.from_user.id
    connections.update_one({"user_id": user_id}, {"$set": {"group_id": group_id}}, upsert=True)
    await message.reply("✅ Group connected successfully.")

@Client.on_message(filters.command("disconnect") & filters.private)
async def disconnect_handler(client, message: Message):
    user_id = message.from_user.id
    connections.delete_one({"user_id": user_id})
    await message.reply("✅ Disconnected from group.")

@Client.on_message(filters.command("connections") & filters.private)
async def list_connections(client, message: Message):
    user_id = message.from_user.id
    data = connections.find_one({"user_id": user_id})
    if data:
        await message.reply(f"🔗 Connected Group ID: `{data['group_id']}`")
    else:
        await message.reply("❌ No active group connection found.")
