from info import *
from utils import *
from asyncio import sleep
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired

@Client.on_message(filters.group & filters.new_chat_members)
async def handle_new_group(bot, message):
    try:
        # Get bot ID
        bot_id = (await bot.get_me()).id
        
        # Check if bot was added
        if bot_id not in [user.id for user in message.new_chat_members]:
            return
        
        # Check if bot has admin permissions
        try:
            bot_member = await bot.get_chat_member(message.chat.id, bot_id)
            if not bot_member.privileges:
                await message.reply(
                    "⚠️ **Please make me admin first!**\n\n"
                    "I need these permissions to function properly:\n"
                    "- Manage Messages (to delete welcome message)\n"
                    "- Restrict Members (for force subscribe)\n"
                    "- Invite Users (to add channels)"
                )
                await bot.leave_chat(message.chat.id)
                return
        except (UserNotParticipant, ChatAdminRequired):
            pass
        
        # Get adding user info
        added_by = message.from_user
        adder_info = f"{added_by.mention} (`{added_by.id}`)" if added_by else "Unknown"
        
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
        welcome_msg = await message.reply(
            f"✨ **Thanks for adding me to {message.chat.title}!**\n\n"
            "🔒 **To get started:**\n"
            "1. Make sure I'm admin with required permissions\n"
            "2. Use /verify to authenticate this group\n"
            "3. Setup force subscribe with /fsub\n\n"
            "❓ Use /help for more information"
        )
        
        # Send log to channel
        log_text = (
            f"#NEW_GROUP\n\n"
            f"🏷 **Group:** [{message.chat.title}]({message.link})\n"
            f"🆔 **ID:** `{message.chat.id}`\n"
            f"👤 **Added by:** {adder_info}\n"
            f"👥 **Members:** `{message.chat.members_count}`"
        )
        await bot.send_message(LOG_CHANNEL, log_text)
        
        # Delete welcome message after delay
        await sleep(60)
        await welcome_msg.delete()
        
    except FloodWait as e:
        await sleep(e.value + 5)
        await handle_new_group(bot, message)
    except Exception as e:
        error_msg = f"❌ **Group Add Error**\n\nGroup: `{message.chat.id}`\nError: `{str(e)}`"
        try:
            await bot.send_message(LOG_CHANNEL, error_msg)
        except:
            pass
