# plugins/broadcast.py
from pyrogram import Client, filters
from pyrogram.types import Message
from info import ADMINS, LOG_CHANNEL
from pymongo import MongoClient
from info import DATABASE_URI

client_db = MongoClient(DATABASE_URI)
db = client_db['filterbot']
sessions = db['sessions']
users = db['users']

@Client.on_message(filters.command("login") & filters.private)
async def login(client, message: Message):
    if str(message.from_user.id) in ADMINS:
        sessions.update_one({"user_id": message.from_user.id}, {"$set": {"active": True}}, upsert=True)
        await message.reply("✅ Login successful.")

@Client.on_message(filters.command("logout") & filters.private)
async def logout(client, message: Message):
    sessions.delete_one({"user_id": message.from_user.id})
    await message.reply("🔒 Logged out.")

@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_handler(client, message: Message):
    if not sessions.find_one({"user_id": message.from_user.id}):
        return await message.reply("❌ You are not logged in.")
    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast.")

    sent = 0
    for user in users.find():
        try:
            await client.copy_message(user['user_id'], message.chat.id, message.reply_to_message.id)
            sent += 1
        except: continue
    await message.reply(f"✅ Broadcast sent to {sent} users.")

@Client.on_message(filters.command("user") & filters.private)
async def user_handler(client, message: Message):
    await message.reply(f"👤 Your ID: `{message.from_user.id}`")

@Client.on_message(filters.command("userc") & filters.private)
async def userc_handler(client, message: Message):
    count = users.count_documents({})
    await message.reply(f"👥 Total users: {count}")

@Client.on_message(filters.command("stats") & filters.private)
async def stats_handler(client, message: Message):
    count = users.count_documents({})
    admins = ", ".join(ADMINS)
    await message.reply(f"📊 Users: {count}\n👮 Admins: {admins}")
