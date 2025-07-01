import logging
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from utils.Helpers import get_group, save_pending_request, delete_after_delay
from utils.Script import script
from info import LOG_CHANNEL

logger = logging.getLogger(__name__)

async def force_sub(bot, message):
    """Force subscribe check without bans/restrictions"""
    try:
        # Skip if no user context
        if not message.from_user:
            return True
            
        group = await get_group(message.chat.id)
        if not group:
            logger.warning(f"Group not found: {message.chat.id}")
            return False

        f_sub = group.get("f_sub")
        admin_id = group.get("user_id")
        
        # Skip if force sub not enabled
        if not f_sub:
            return True

        try:
            # Get force sub channel
            channel = await bot.get_chat(f_sub)
            invite_link = channel.invite_link
            
            # Check user status
            member = await bot.get_chat_member(f_sub, message.from_user.id)
            status = member.status
            
            # Allow if user is member
            if status in [
                enums.ChatMemberStatus.ADMINISTRATOR,
                enums.ChatMemberStatus.OWNER,
                enums.ChatMemberStatus.MEMBER
            ]:
                return True
                
        except UserNotParticipant:
            pass  # Will handle below
            
        # User not in channel - store search request
        await save_pending_request(
            message.from_user.id,
            message.chat.id,
            message.text
        )
        
        # Send join request
        join_msg = await message.reply(
            script.HELP,  # Using your custom HELP message
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Join Channel", url=invite_link)],
                [InlineKeyboardButton("♻️ Try Again", callback_data=f"retry_search_{message.from_user.id}")]
            ])
        )
        
        # Schedule message deletion
        asyncio.create_task(delete_after_delay(join_msg, 60))
        return False
            
    except Exception as e:
        logger.error(f"Force sub error: {str(e)}")
        # Notify admin of critical errors
        if admin_id:
            await bot.send_message(
                admin_id,
                f"⚠️ Force Sub Error\n\nGroup: {message.chat.title}\nError: {str(e)}"
            )
        return True  # Allow search on errors

@Client.on_callback_query(filters.regex(r"^retry_search_"))
async def handle_retry_search(bot, update):
    """Handle search retry after joining channel"""
    try:
        user_id = int(update.data.split("_")[-1])
        
        # Verify user
        if update.from_user.id != user_id:
            await update.answer("❌ This isn't for you!", show_alert=True)
            return
            
        # Get pending request
        request = await get_pending_request(user_id)
        if not request:
            await update.answer("🔍 No pending request", show_alert=True)
            await update.message.delete()
            return
            
        # Check if user joined
        group = await get_group(request["chat_id"])
        if not group or not group.get("f_sub"):
            await update.answer("❌ Force sub not configured", show_alert=True)
            return
            
        try:
            member = await bot.get_chat_member(group["f_sub"], user_id)
            if member.status not in [
                enums.ChatMemberStatus.ADMINISTRATOR,
                enums.ChatMemberStatus.OWNER,
                enums.ChatMemberStatus.MEMBER
            ]:
                # Not joined
                await update.answer("❌ Please join channel first!", show_alert=True)
                return
        except UserNotParticipant:
            await update.answer("❌ You haven't joined yet!", show_alert=True)
            return
            
        # Process search
        await update.answer("🔍 Searching...")
        await update.message.delete()
        
        # Trigger search handler
        from plugins.Search import perform_search
        await perform_search(bot, request["chat_id"], user_id, request["query"])
        
    except Exception as e:
        logger.error(f"Retry search error: {str(e)}")
        await update.answer("⚠️ Error occurred!", show_alert=True)
