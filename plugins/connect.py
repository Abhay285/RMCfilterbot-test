import logging
from pyrogram import Client, filters
from utils.Helpers import get_group, update_group
from utils.Script import script
from info import LOG_CHANNEL

logger = logging.getLogger(__name__)

@Client.on_message(filters.group & filters.command("connect"))
async def connect_channel(bot, message):
    try:
        # Validate command
        if len(message.command) < 2:
            return await message.reply("❌ Format: /connect channel_id")
        
        # Get group
        group = await get_group(message.chat.id)
        if not group:
            return await bot.leave_chat(message.chat.id)
        
        # Check permissions
        if message.from_user.id != group["user_id"]:
            return await message.reply(f"⚠️ Only {group['user_name']} can do this")
        
        # Get channel ID
        try:
            channel_id = int(message.command[1])
        except ValueError:
            return await message.reply("❌ Invalid Channel ID! Must be integer")
        
        # Check if already connected
        channels = group.get("channels", [])
        if channel_id in channels:
            return await message.reply("⚠️ Channel already connected")
        
        # Add channel
        channels.append(channel_id)
        await update_group(message.chat.id, {"channels": channels})
        
        # Get channel info
        try:
            channel = await bot.get_chat(channel_id)
            channel_link = f"[{channel.title}]({channel.invite_link})"
        except:
            channel_link = f"`{channel_id}`"
        
        # Send success
        await message.reply(f"✅ Connected to channel {channel_link}")
        
        # Log
        log_text = (
            f"#NEW_CONNECTION\n\n"
            f"👤 User: {message.from_user.mention}\n"
            f"👥 Group: {message.chat.title} ({message.chat.id})\n"
            f"📢 Channel: {channel_link}"
        )
        await bot.send_message(LOG_CHANNEL, log_text)
        
    except Exception as e:
        logger.error(f"Connect error: {str(e)}")
        await message.reply("⚠️ An error occurred!")

@Client.on_message(filters.group & filters.command("disconnect"))
async def disconnect_channel(bot, message):
    try:
        # Validate command
        if len(message.command) < 2:
            return await message.reply("❌ Format: /disconnect channel_id")
        
        # Get group
        group = await get_group(message.chat.id)
        if not group:
            return await bot.leave_chat(message.chat.id)
        
        # Check permissions
        if message.from_user.id != group["user_id"]:
            return await message.reply(f"⚠️ Only {group['user_name']} can do this")
        
        # Get channel ID
        try:
            channel_id = int(message.command[1])
        except ValueError:
            return await message.reply("❌ Invalid Channel ID! Must be integer")
        
        # Remove channel
        channels = group.get("channels", [])
        if channel_id not in channels:
            return await message.reply("⚠️ Channel not connected")
        
        channels.remove(channel_id)
        await update_group(message.chat.id, {"channels": channels})
        
        # Get channel info
        try:
            channel = await bot.get_chat(channel_id)
            channel_link = f"[{channel.title}]({channel.invite_link})"
        except:
            channel_link = f"`{channel_id}`"
        
        # Send success
        await message.reply(f"✅ Disconnected from channel {channel_link}")
        
        # Log
        log_text = (
            f"#DISCONNECTION\n\n"
            f"👤 User: {message.from_user.mention}\n"
            f"👥 Group: {message.chat.title} ({message.chat.id})\n"
            f"📢 Channel: {channel_link}"
        )
        await bot.send_message(LOG_CHANNEL, log_text)
        
    except Exception as e:
        logger.error(f"Disconnect error: {str(e)}")
        await message.reply("⚠️ An error occurred!")

@Client.on_message(filters.group & filters.command("connections"))
async def list_connections(bot, message):
    try:
        group = await get_group(message.chat.id)
        if not group:
            return
        
        # Check permissions
        if message.from_user.id != group["user_id"]:
            return await message.reply(f"⚠️ Only {group['user_name']} can do this")
        
        channels = group.get("channels", [])
        f_sub = group.get("f_sub")
        
        if not channels and not f_sub:
            return await message.reply("❌ No connections configured")
        
        response = "🔗 **Group Connections:**\n\n"
        
        # List channels
        for channel_id in channels:
            try:
                chat = await bot.get_chat(channel_id)
                response += f"📢 Channel: [{chat.title}]({chat.invite_link})\n🆔 ID: `{channel_id}`\n\n"
            except:
                response += f"📢 Channel: `{channel_id}` (Invalid)\n\n"
        
        # List FSub channel
        if f_sub:
            try:
                chat = await bot.get_chat(f_sub)
                response += f"🔔 Force Subscribe: [{chat.title}]({chat.invite_link})\n🆔 ID: `{f_sub}`"
            except:
                response += f"🔔 Force Subscribe: `{f_sub}` (Invalid)"
        
        await message.reply(response, disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Connections error: {str(e)}")
        await message.reply("⚠️ An error occurred!")
