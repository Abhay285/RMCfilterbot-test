import asyncio
import logging
import time
from info import *
from utils import *
from plugins.generate import database
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import FloodWait

# Configure logging
logger = logging.getLogger(__name__)

# Cache for user sessions to improve speed
session_cache = {}
last_cache_refresh = 0
CACHE_TTL = 3600  # 1 hour

async def get_user_session():
    """Get user session with caching"""
    global session_cache, last_cache_refresh
    
    current_time = time.time()
    if current_time - last_cache_refresh > CACHE_TTL or not session_cache:
        vj = database.find_one({"chat_id": ADMIN})
        session_cache = vj
        last_cache_refresh = current_time
    
    return session_cache

async def send_results_with_delete(bot, chat_id, text, reply_to=None):
    """Send results and schedule deletion after 40 seconds"""
    try:
        msg = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to,
            disable_web_page_preview=True
        )
        asyncio.create_task(delete_after_delay(msg, 40))
        return msg
    except Exception as e:
        logger.error(f"Error sending results: {str(e)}")

async def delete_after_delay(message: Message, delay):
    """Delete message after delay with error handling"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {str(e)}")

async def perform_fast_channel_search(user_client, channels, query):
    """Fast parallel search in connected channels"""
    results = {}
    search_tasks = []
    
    # Create search tasks for all channels
    for channel in channels:
        task = user_client.search_messages(chat_id=channel, query=query, limit=5)
        search_tasks.append(task)
    
    # Run all searches concurrently
    channel_results = await asyncio.gather(*search_tasks, return_exceptions=True)
    
    # Process results
    for channel, messages in zip(channels, channel_results):
        if isinstance(messages, Exception):
            logger.error(f"Search error in {channel}: {str(messages)}")
            continue
            
        async for msg in messages:
            content = msg.text or msg.caption or ""
            name = content.split("\n")[0] if content else "Untitled"
            
            if name not in results:
                results[name] = f"🔗 [{name}]({msg.link})\n"
    
    return "".join(results.values())

@Client.on_message(filters.group & filters.incoming & ~filters.command(["verify", "connect", "id", "start"]))
async def fast_search_handler(bot, message):
    """Handle search requests with improved speed"""
    try:
        start_time = time.time()
        
        # Check if query is valid
        query = message.text.strip()
        if len(query) < 3:
            return
        
        # Get user session
        vj = await get_user_session()
        if not vj:
            await message.reply("🔒 **Admin session not found!** Contact admin to log in.")
            return
        
        # Check force subscription
        f_sub = await force_sub(bot, message)
        if not f_sub:
            return
        
        # Get group channels
        group_data = await get_group(message.chat.id)
        if not group_data or not group_data.get("channels"):
            return
        
        # Connect user client
        async with Client(
            "user_session", 
            session_string=vj['session'], 
            api_hash=API_HASH, 
            api_id=API_ID
        ) as user_client:
            # Perform fast parallel search
            channel_results = await perform_fast_channel_search(user_client, group_data["channels"], query)
            
            if channel_results:
                # Format results
                head = (
                    f"⚡ **Results for: `{query}`**\n"
                    f"👤 Requested by: {message.from_user.mention}\n\n"
                )
                full_text = head + channel_results + "\n✨ Powered by @RMCBACKUP"
                
                # Send results with auto-delete
                await send_results_with_delete(
                    bot, message.chat.id, full_text, reply_to=message.id
                )
            else:
                # No results found
                no_result_msg = (
                    f"🔍 **No results found for: `{query}`**\n\n"
                    "Request admin to add this content:"
                )
                
                msg = await message.reply(
                    no_result_msg,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📬 Request Content", callback_data=f"request_{query}")
                    ]])
                )
                asyncio.create_task(delete_after_delay(msg, 40))
        
        logger.info(f"Search completed in {time.time() - start_time:.2f} seconds")
        
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        await fast_search_handler(bot, message)
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        error_msg = await message.reply("⚠️ An error occurred. Please try again later.")
        asyncio.create_task(delete_after_delay(error_msg, 20))

@Client.on_callback_query(filters.regex(r"^request_"))
async def handle_request(bot, update):
    """Handle content requests to admin"""
    try:
        # Verify user
        if update.from_user.id != update.message.reply_to_message.from_user.id:
            await update.answer("❌ This action isn't for you!", show_alert=True)
            return
        
        # Get requested content
        requested_content = update.data.split("_", 1)[1]
        
        # Get group admin
        group_data = await get_group(update.message.chat.id)
        if not group_data:
            await update.answer("❌ Group data not found!", show_alert=True)
            return
        
        admin_id = group_data["user_id"]
        
        # Prepare request message
        request_text = (
            f"📬 **Content Request**\n\n"
            f"👤 From: {update.from_user.mention} (`{update.from_user.id}`)\n"
            f"👥 Group: {update.message.chat.title} (`{update.message.chat.id}`)\n"
            f"🔍 Requested: `{requested_content}`"
        )
        
        # Send request to admin
        await bot.send_message(chat_id=admin_id, text=request_text)
        
        await update.answer("✅ Request sent to group admin!", show_alert=True)
        
        # Delete request message after 5 seconds
        await asyncio.sleep(5)
        await update.message.delete()
    
    except Exception as e:
        logger.error(f"Request error: {str(e)}", exc_info=True)
        await update.answer("⚠️ Failed to send request!", show_alert=True)
