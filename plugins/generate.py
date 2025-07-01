import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from config import DATABASE_URL, DATABASE_NAME, CHANNELS, ADMINS

# Initialize database connection
client = MongoClient(DATABASE_URL)
db = client[DATABASE_NAME]
col = db["Posts"]

# Global database instance
database = col

async def index_post(message: Message):
    """Index a single post into the database"""
    post = {
        "id": message.id,
        "chat": message.chat.id,
        "caption": message.caption.html if message.caption else "",
        "file_type": None,
        "file_id": None,
        "date": message.date
    }
    
    # Determine media type
    if message.video:
        post["file_type"] = "video"
        post["file_id"] = message.video.file_id
    elif message.document:
        post["file_type"] = "document"
        post["file_id"] = message.document.file_id
    elif message.audio:
        post["file_type"] = "audio"
        post["file_id"] = message.audio.file_id
    elif message.photo:
        post["file_type"] = "photo"
        post["file_id"] = message.photo.file_id
    
    # Insert into database
    database.insert_one(post)

@Client.on_message(filters.chat(CHANNELS) & (filters.media | filters.document))
async def auto_index(client, message: Message):
    """Automatically index new posts from monitored channels"""
    try:
        await index_post(message)
        # Optional: Send confirmation to admin
        await client.send_message(
            ADMINS[0], 
            f"✅ Auto-indexed post from {message.chat.title}\nPost ID: {message.id}"
        )
    except Exception as e:
        error_msg = f"❌ Auto-index failed for {message.chat.title} - Post {message.id}\nError: {str(e)}"
        await client.send_message(ADMINS[0], error_msg)
        print(error_msg)

@Client.on_message(filters.command("generate") & filters.user(ADMINS))
async def manual_generate(client, message: Message):
    """Manual database generation command"""
    status_msg = await message.reply("🔄 Starting database regeneration...")
    total_indexed = 0
    errors = 0
    
    # Clear existing data
    database.delete_many({})
    
    for channel in CHANNELS:
        try:
            await status_msg.edit(f"⏳ Processing channel {channel}...")
            # Fetch all messages from channel
            async for msg in client.search_messages(channel):
                if msg.media or msg.document:
                    try:
                        await index_post(msg)
                        total_indexed += 1
                    except Exception as e:
                        errors += 1
                        print(f"Error indexing {msg.id} in {channel}: {str(e)}")
        except Exception as e:
            error_msg = f"❌ Error processing channel {channel}: {str(e)}"
            await client.send_message(ADMINS[0], error_msg)
            print(error_msg)
            errors += 1
    
    completion_msg = (
        f"✅ Database regeneration complete!\n"
        f"• Total posts indexed: {total_indexed}\n"
        f"• Channels processed: {len(CHANNELS)}\n"
        f"• Errors encountered: {errors}"
    )
    await status_msg.edit(completion_msg)
    await client.send_message(ADMINS[0], completion_msg)

@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def show_stats(client, message: Message):
    """Show database statistics"""
    total_posts = database.count_documents({})
    channels_stats = []
    
    for channel in CHANNELS:
        try:
            chat = await client.get_chat(channel)
            count = database.count_documents({"chat": channel})
            channels_stats.append(f"• {chat.title}: {count} posts")
        except:
            channels_stats.append(f"• Unknown channel {channel}: {count} posts")
    
    stats_message = (
        "📊 Database Statistics:\n"
        f"Total indexed posts: {total_posts}\n"
        "Per channel:\n" + "\n".join(channels_stats)
    )
    
    await message.reply(stats_message)
