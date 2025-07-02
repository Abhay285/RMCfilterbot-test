import logging
import asyncio
from pyrogram import Client, filters
from utils.helpers import add_group
from utils.script import script
from info import LOG_CHANNEL

logger = logging.getLogger(__name__)

@Client.on_message(filters.group & filters.new_chat_members)
async def new_group_handler(bot, message):
    try:
        # Check if bot was added
        bot_id = (await bot.get_me()).id
        if bot_id not in [user.id for user in message.new_chat_members]:
            return
        
        # Get adder info
        added_by = message.from_user
        adder_info = f"{added_by.mention} ({added_by.id})" if added_by else "Unknown"
        
        # Add group to database
        await add_group(
            group_id=message.chat.id,
            group_name=message.chat.title,
            user_name=added_by.first_name if added_by else "Unknown",
            user_id=added_by.id if added_by else 0,
            channels=[],
            f_sub=False,
            verified=False
        )
        
        # Send welcome message
        welcome_msg = await message.reply(script.START.format(message.chat.title))
        await asyncio.sleep(60)
        await welcome_msg.delete()
        
        # Log to channel
        log_text = (
            f"#NEW_GROUP\n\n"
            f"🏷️ Group: {message.chat.title}\n"
            f"🆔 ID: `{message.chat.id}`\n"
            f"👤 Added by: {adder_info}\n"
            f"👥 Members: {message.chat.members_count}"
        )
        await bot.send_message(LOG_CHANNEL, log_text)
        
    except Exception as e:
        logger.error(f"New group error: {str(e)}")
