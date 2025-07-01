import logging
import asyncio
from pyrogram import Client, filters
from utils.Helpers import get_group, perform_fast_channel_search, delete_after_delay
from plugins.Fsub import force_sub
from info import API_ID, API_HASH
from plugins.generate import database  # Your session manager

logger = logging.getLogger(__name__)

async def perform_search(bot, chat_id, user_id, query):
    """Actual search implementation"""
    try:
        # Get group
        group = await get_group(chat_id)
        if not group or not group.get("channels"):
            return
            
        # Get user session
        vj = database.find_one({"chat_id": ADMIN})
        if not vj:
            return
            
        # Connect user client
        async with Client(
            "user_session", 
            session_string=vj['session'], 
            api_hash=API_HASH, 
            api_id=API_ID
        ) as user_client:
            # Perform search
            results = await perform_fast_channel_search(
                user_client, 
                group["channels"], 
                query
            )
            
            if results:
                # Format response
                response = (
                    f"🔍 Results for: `{query}`\n\n"
                    f"{results}\n\n"
                    f"✨ Powered by @RMCBACKUP"
                )
                msg = await bot.send_message(chat_id, response)
                asyncio.create_task(delete_after_delay(msg, 40))
            else:
                # No results
                msg = await bot.send_message(
                    chat_id,
                    f"🔍 No results found for: `{query}`\n\nRequest admin to add content:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📬 Request Content", callback_data=f"request_{query}")
                    ]])
                )
                asyncio.create_task(delete_after_delay(msg, 40))
                
    except Exception as e:
        logger.error(f"Search error: {str(e)}")

@Client.on_message(filters.group & filters.text & ~filters.command)
async def search_handler(bot, message):
    """Main search handler"""
    # First check force sub
    if not await force_sub(bot, message):
        return
        
    # Then process search
    await perform_search(
        bot,
        message.chat.id,
        message.from_user.id,
        message.text
    )

@Client.on_callback_query(filters.regex(r"^request_"))
async def handle_request(bot, update):
    """Handle content requests"""
    try:
        # Get requested content
        requested_content = update.data.split("_", 1)[1]
        
        # Get group admin
        group = await get_group(update.message.chat.id)
        if not group:
            return
            
        admin_id = group["user_id"]
        
        # Send request
        await bot.send_message(
            admin_id,
            f"📬 Content Request\n\n"
            f"👤 From: {update.from_user.mention}\n"
            f"👥 Group: {update.message.chat.title}\n"
            f"🔍 Requested: `{requested_content}`"
        )
        
        await update.answer("✅ Request sent to admin!", show_alert=True)
        await update.message.delete()
        
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        await update.answer("⚠️ Failed to send request!", show_alert=True)
