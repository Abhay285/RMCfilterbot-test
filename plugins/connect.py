from info import *
from utils import *
from plugins.generate import database
from pyrogram import Client, filters, enums
from pyrogram.errors import (
    UserAlreadyParticipant,
    ChannelPrivate,
    ChatAdminRequired,
    PeerIdInvalid
)

async def get_user_session():
    """Fetch user session from database"""
    return await database.find_one({"chat_id": ADMIN})

@Client.on_message(filters.group & filters.command("connect"))
async def connect_group(bot, message):
    # Initial setup
    if len(message.command) < 2:
        return await message.reply("❌ **Format:** `/connect channel_id`")
    
    m = await message.reply("🔁 **Connecting...**")
    
    # Fetch user session
    user_data = await get_user_session()
    if not user_data:
        return await m.edit("**⚠️ Contact Admin to log in first!**")
    
    # Get group details
    group = await get_group(message.chat.id)
    if not group:
        return await bot.leave_chat(message.chat.id)
    
    # Permission check
    if message.from_user.id != group["user_id"]:
        return await m.edit(f"❌ Only **{group['user_name']}** can use this command")
    
    # Verification check
    if not group["verified"]:
        return await m.edit("🔒 **Unverified group!** Use /verify first")

    try:
        channel_id = int(message.command[1])
        channels = group.get("channels", [])
        
        # Check if channel already connected
        if channel_id in channels:
            return await m.edit("⚠️ Channel already connected!")
    except ValueError:
        return await m.edit("❌ **Invalid Channel ID!** Must be integer")

    try:
        # Get channel and group objects
        channel = await bot.get_chat(channel_id)
        current_group = await bot.get_chat(message.chat.id)
        
        # Join channel with user account
        async with Client(
            "user_session", 
            session_string=user_data['session'], 
            api_hash=API_HASH, 
            api_id=API_ID
        ) as user_client:
            try:
                await user_client.join_chat(channel.invite_link)
            except UserAlreadyParticipant:
                pass
        
        # Update database
        channels.append(channel_id)
        await update_group(message.chat.id, {"channels": channels})
        
        # Send success message
        success_msg = (
            f"✅ **Successfully connected to [{channel.title}]({channel.invite_link})!**\n\n"
            f"• **Channel ID:** `{channel_id}`\n"
            f"• **Total Connections:** `{len(channels)}`"
        )
        await m.edit(success_msg, disable_web_page_preview=True)
        
        # Log to channel
        log_msg = (
            f"#NEW_CONNECTION\n\n"
            f"👤 **User:** {message.from_user.mention} (`{message.from_user.id}`)\n"
            f"👥 **Group:** [{current_group.title}]({current_group.invite_link}) (`{message.chat.id}`)\n"
            f"📢 **Channel:** [{channel.title}]({channel.invite_link}) (`{channel_id}`)"
        )
        await bot.send_message(LOG_CHANNEL, log_msg)
        
    except (ChannelPrivate, ChatAdminRequired):
        await m.edit("❌ **Bot needs admin rights in channel!**")
    except PeerIdInvalid:
        await m.edit("❌ **Invalid Channel ID!**")
    except Exception as e:
        await m.edit(f"❌ **Error:** `{str(e)}`")
        await bot.send_message(LOG_CHANNEL, f"#CONNECT_ERROR\n\n`{e}`")

@Client.on_message(filters.group & filters.command("disconnect"))
async def disconnect_group(bot, message):
    # Initial setup
    if len(message.command) < 2:
        return await message.reply("❌ **Format:** `/disconnect channel_id`")
    
    m = await message.reply("🔁 **Disconnecting...**")
    
    # Get group details
    group = await get_group(message.chat.id)
    if not group:
        return await bot.leave_chat(message.chat.id)
    
    # Permission check
    if message.from_user.id != group["user_id"]:
        return await m.edit(f"❌ Only **{group['user_name']}** can use this command")
    
    try:
        channel_id = int(message.command[1])
        channels = group.get("channels", [])
        
        # Check if channel exists
        if channel_id not in channels:
            return await m.edit("❌ Channel not connected!")
    except ValueError:
        return await m.edit("❌ **Invalid Channel ID!** Must be integer")

    try:
        # Get channel and group objects
        channel = await bot.get_chat(channel_id)
        current_group = await bot.get_chat(message.chat.id)
        
        # Leave channel with user account
        user_data = await get_user_session()
        if user_data:
            async with Client(
                "user_session", 
                session_string=user_data['session'], 
                api_hash=API_HASH, 
                api_id=API_ID
            ) as user_client:
                await user_client.leave_chat(channel_id)
        
        # Update database
        channels.remove(channel_id)
        await update_group(message.chat.id, {"channels": channels})
        
        # Send success message
        success_msg = (
            f"✅ **Disconnected from [{channel.title}]({channel.invite_link})!**\n\n"
            f"• **Channel ID:** `{channel_id}`\n"
            f"• **Remaining Connections:** `{len(channels)}`"
        )
        await m.edit(success_msg, disable_web_page_preview=True)
        
        # Log to channel
        log_msg = (
            f"#DISCONNECTION\n\n"
            f"👤 **User:** {message.from_user.mention} (`{message.from_user.id}`)\n"
            f"👥 **Group:** [{current_group.title}]({current_group.invite_link}) (`{message.chat.id}`)\n"
            f"📢 **Channel:** [{channel.title}]({channel.invite_link}) (`{channel_id}`)"
        )
        await bot.send_message(LOG_CHANNEL, log_msg)
        
    except (ChannelPrivate, ChatAdminRequired):
        await m.edit("❌ **Failed to leave channel!**")
    except Exception as e:
        await m.edit(f"❌ **Error:** `{str(e)}`")
        await bot.send_message(LOG_CHANNEL, f"#DISCONNECT_ERROR\n\n`{e}`")

@Client.on_message(filters.group & filters.command("connections"))
async def show_connections(bot, message):
    # Get group details
    group = await get_group(message.chat.id)
    if not group:
        return await bot.leave_chat(message.chat.id)
    
    # Permission check
    if message.from_user.id != group["user_id"]:
        return await message.reply(f"❌ Only **{group['user_name']}** can use this command")
    
    channels = group.get("channels", [])
    f_sub = group.get("f_sub")
    
    if not channels and not f_sub:
        return await message.reply("🔌 **No connections found!**")
    
    response = "🔗 **Group Connections:**\n\n"
    
    # Process channels
    for idx, channel_id in enumerate(channels, 1):
        try:
            chat = await bot.get_chat(channel_id)
            response += (
                f"{idx}. 📢 **Channel:** [{chat.title}]({chat.invite_link})\n"
                f"   • **ID:** `{channel_id}`\n"
                f"   • **Members:** `{chat.members_count}`\n\n"
            )
        except Exception:
            response += f"{idx}. ❌ **Invalid Channel:** `{channel_id}`\n\n"
    
    # Process FSub channel
    if f_sub:
        try:
            f_chat = await bot.get_chat(f_sub)
            response += (
                "🔔 **Force Subscribe:**\n"
                f"   • **Channel:** [{f_chat.title}]({f_chat.invite_link})\n"
                f"   • **ID:** `{f_sub}`\n"
            )
        except Exception:
            response += "🔔 **Force Subscribe:**\n   • ❌ Invalid Channel\n"
    
    await message.reply(response, disable_web_page_preview=True)
