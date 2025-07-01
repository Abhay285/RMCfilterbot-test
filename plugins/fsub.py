from info import *
from utils import *
from pyrogram import Client, filters, enums
from pyrogram.types import ChatPermissions
from pyrogram.errors import (
    UserNotParticipant,
    ChannelPrivate,
    ChatAdminRequired,
    UserAdminInvalid
)

async def validate_fsub_channel(bot, channel_id, group_id):
    """Validate if bot has required permissions in FSub channel"""
    try:
        # Check if bot is admin in channel
        chat = await bot.get_chat(channel_id)
        me = await chat.get_member(bot.me.id)
        
        if not me.privileges:
            return False, "❌ Bot needs admin rights in channel"
        
        # Check if bot has invite link permission
        if not me.privileges.can_invite_users:
            return False, "❌ Bot needs 'Invite Users' permission in channel"
        
        # Check if channel is valid
        if chat.type not in (enums.ChatType.CHANNEL, enums.ChatType.SUPERGROUP):
            return False, "❌ FSub must be a channel or supergroup"
        
        # Check if bot is admin in current group
        group = await bot.get_chat(group_id)
        group_me = await group.get_member(bot.me.id)
        
        if not group_me.privileges:
            return False, "❌ Bot needs admin rights in this group"
        
        # Check if bot can restrict users
        if not group_me.privileges.can_restrict_members:
            return False, "❌ Bot needs 'Restrict Members' permission in group"
        
        return True, chat
    
    except (ChannelPrivate, ChatAdminRequired):
        return False, "❌ Bot is not admin in channel"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

@Client.on_message(filters.group & filters.command("fsub"))
async def set_fsub_channel(bot, message):
    # Validate command format
    if len(message.command) < 2:
        return await message.reply("❌ **Format:** `/fsub channel_id`")
    
    try:
        channel_id = int(message.command[1])
    except ValueError:
        return await message.reply("❌ **Invalid Channel ID!** Must be integer")
    
    m = await message.reply("🔒 **Setting up Force Subscribe...**")
    
    # Get group info
    group = await get_group(message.chat.id)
    if not group:
        return await bot.leave_chat(message.chat.id)
    
    # Permission check
    if message.from_user.id != group["user_id"]:
        return await m.edit(f"❌ Only **{group['user_name']}** can use this command")
    
    # Verification check
    if not group["verified"]:
        return await m.edit("🔒 **Unverified group!** Use /verify first")
    
    # Validate channel
    valid, response = await validate_fsub_channel(bot, channel_id, message.chat.id)
    if not valid:
        return await m.edit(response)
    
    # Update database
    await update_group(message.chat.id, {"f_sub": channel_id})
    
    # Get group info for logging
    current_group = await bot.get_chat(message.chat.id)
    
    # Send success message
    success_msg = (
        f"✅ **Force Subscribe Enabled!**\n\n"
        f"• **Channel:** [{response.title}]({response.invite_link})\n"
        f"• **Channel ID:** `{channel_id}`\n\n"
        f"All new members must join this channel to participate."
    )
    await m.edit(success_msg, disable_web_page_preview=True)
    
    # Log to channel
    log_msg = (
        f"#NEW_FSUB\n\n"
        f"👤 **User:** {message.from_user.mention} (`{message.from_user.id}`)\n"
        f"👥 **Group:** [{current_group.title}]({current_group.invite_link}) (`{message.chat.id}`)\n"
        f"📢 **Channel:** [{response.title}]({response.invite_link}) (`{channel_id}`)"
    )
    await bot.send_message(LOG_CHANNEL, log_msg)

@Client.on_message(filters.group & filters.command("nofsub"))
async def remove_fsub_channel(bot, message):
    m = await message.reply("🔓 **Removing Force Subscribe...**")
    
    # Get group info
    group = await get_group(message.chat.id)
    if not group:
        return await bot.leave_chat(message.chat.id)
    
    # Permission check
    if message.from_user.id != group["user_id"]:
        return await m.edit(f"❌ Only **{group['user_name']}** can use this command")
    
    # Check if FSub exists
    if not group.get("f_sub"):
        return await m.edit("❌ **No Force Subscribe configured!**")
    
    # Get channel info for logging
    try:
        channel = await bot.get_chat(group["f_sub"])
    except Exception:
        channel = None
    
    # Update database
    await update_group(message.chat.id, {"f_sub": None})
    
    # Get group info for logging
    current_group = await bot.get_chat(message.chat.id)
    
    # Send success message
    success_msg = "✅ **Force Subscribe Disabled!**\n\nMembers can now participate without joining any channel."
    await m.edit(success_msg)
    
    # Log to channel
    log_msg = (
        f"#REMOVE_FSUB\n\n"
        f"👤 **User:** {message.from_user.mention} (`{message.from_user.id}`)\n"
        f"👥 **Group:** [{current_group.title}]({current_group.invite_link}) (`{message.chat.id}`)\n"
    )
    
    if channel:
        log_msg += f"📢 **Channel:** [{channel.title}]({channel.invite_link}) (`{group['f_sub']}`)"
    else:
        log_msg += f"📢 **Channel ID:** `{group['f_sub']}`"
    
    await bot.send_message(LOG_CHANNEL, log_msg)

@Client.on_callback_query(filters.regex(r"^checksub_"))
async def handle_fsub_callback(bot, query):
    try:
        # Extract data from callback
        user_id = int(query.data.split("_")[-1])
        group_id = query.message.chat.id
        
        # Verify user identity
        if query.from_user.id != user_id:
            await query.answer("⛔ This button isn't for you!", show_alert=True)
            return
        
        # Get group info
        group = await get_group(group_id)
        if not group or not group.get("f_sub"):
            await query.answer("❌ Configuration error - try again later", show_alert=True)
            return
        
        # Check channel membership
        try:
            await bot.get_chat_member(group["f_sub"], user_id)
            is_member = True
        except UserNotParticipant:
            is_member = False
        except Exception as e:
            await query.answer(f"⚠️ Error: {str(e)}", show_alert=True)
            return
        
        # Handle based on membership status
        if not is_member:
            await query.answer(
                "🔒 Join the required channel first!",
                show_alert=True
            )
        else:
            # Grant full permissions
            permissions = ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_send_polls=True,
                can_add_web_page_previews=True,
                can_invite_users=True,
                can_change_info=False,
                can_pin_messages=False
            )
            
            try:
                await bot.restrict_chat_member(
                    chat_id=group_id,
                    user_id=user_id,
                    permissions=permissions
                )
                await query.message.delete()
            except UserAdminInvalid:
                await query.answer("✅ Verified! You're an admin", show_alert=True)
            except Exception as e:
                await query.answer(f"⚠️ Error: {str(e)}", show_alert=True)
    
    except Exception as e:
        logging.error(f"FSub callback error: {str(e)}")
        await query.answer("⚠️ System error - contact admin", show_alert=True)
