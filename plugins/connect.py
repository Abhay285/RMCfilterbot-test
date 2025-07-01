import logging
from pyrogram import Client, filters
from utils.Helpers import get_group, update_group
from utils.Script import script
from info import LOG_CHANNEL

logger = logging.getLogger(__name__)

@Client.on_message(filters.group & filters.command("connect"))
async def connect_channel(bot, message):
    try:
        if len(message.command) < 2:
            return await message.reply("❌ Format: /connect channel_id")
        
        group = await get_group(message.chat.id)
        if not group:
            return await bot.leave_chat(message.chat.id)
        
        if message.from_user.id != group["user_id"]:
            return await message.reply(f"⚠️ Only {group['user_name']} can do this")
        
        try:
            channel_id = int(message.command[1])
        except ValueError:
            return await message.reply("❌ Invalid Channel ID! Must be integer")
        
        channels = group.get("channels", [])
        if channel_id in channels:
            return await message.reply("⚠️ Channel already connected")
        
        channels.append(channel_id)
        await update_group(message.chat.id, {"channels": channels})
        
        try:
            channel = await bot.get_chat(channel_id)
            channel_link = f"[{channel.title}]({channel.invite_link})"
        except:
            channel_link = f"`{channel_id}`"
        
        await message.reply(f"✅ Connected to channel {channel_link}")
        
        log_text = f"#NEW_CONNECTION\n\n👤 User: {message.from_user.mention}\n👥 Group: {message.chat.title}\n📢 Channel: {channel_link}"
        await bot.send_message(LOG_CHANNEL, log_text)
        
    except Exception as e:
        logger.error(f"Connect error: {e}")
        await message.reply("⚠️ An error occurred!")

@Client.on_message(filters.group & filters.command("disconnect"))
async def disconnect_channel(bot, message):
    try:
        if len(message.command) < 2:
            return await message.reply("❌ Format: /disconnect channel_id")
        
        group = await get_group(message.chat.id)
        if not group:
            return await bot.leave_chat(message.chat.id)
        
        if message.from_user.id != group["user_id"]:
            return await message.reply(f"⚠️ Only {group['user_name']} can do this")
        
        try:
            channel_id = int(message.command[1])
        except ValueError:
            return await message.reply("❌ Invalid Channel ID! Must be integer")
        
        channels = group.get("channels", [])
        if channel_id not in channels:
            return await message.reply("⚠️ Channel not connected")
        
        channels.remove(channel_id)
        await update_group(message.chat.id, {"channels": channels})
        
        try:
            channel = await bot.get_chat(channel_id)
            channel_link = f"[{channel.title}]({channel.invite_link})"
        except:
            channel_link = f"`{channel_id}`"
        
        await message.reply(f"✅ Disconnected from channel {channel_link}")
        log_text = f"#DISCONNECTION\n\n👤 User: {message.from_user.mention}\n👥 Group: {message.chat.title}\n📢 Channel: {channel_link}"
        await bot.send_message(LOG_CHANNEL, log_text)
        
    except Exception as e:
        logger.error(f"Disconnect error: {e}")
        await message.reply("⚠️ An error occurred!")

@Client.on_message(filters.group & filters.command("fsub"))
async def set_fsub(bot, message):
    try:
        if len(message.command) < 2:
            return await message.reply("❌ Format: /fsub channel_id")
        
        group = await get_group(message.chat.id)
        if not group:
            return await bot.leave_chat(message.chat.id)
        
        if message.from_user.id != group["user_id"]:
            return await message.reply(f"⚠️ Only {group['user_name']} can do this")
        
        try:
            channel_id = int(message.command[1])
        except ValueError:
            return await message.reply("❌ Invalid Channel ID! Must be integer")
        
        await update_group(message.chat.id, {"f_sub": channel_id})
        
        try:
            channel = await bot.get_chat(channel_id)
            channel_link = f"[{channel.title}]({channel.invite_link})"
        except:
            channel_link = f"`{channel_id}`"
        
        await message.reply(f"✅ Force Subscribe set to {channel_link}")
        log_text = f"#FSUB_SET\n\n👤 User: {message.from_user.mention}\n👥 Group: {message.chat.title}\n📢 Channel: {channel_link}"
        await bot.send_message(LOG_CHANNEL, log_text)
        
    except Exception as e:
        logger.error(f"Set FSub error: {e}")
        await message.reply("⚠️ An error occurred!")

@Client.on_message(filters.group & filters.command("nofsub"))
async def remove_fsub(bot, message):
    try:
        group = await get_group(message.chat.id)
        if not group:
            return await bot.leave_chat(message.chat.id)
        
        if message.from_user.id != group["user_id"]:
            return await message.reply(f"⚠️ Only {group['user_name']} can do this")
        
        if not group.get("f_sub"):
            return await message.reply("❌ Force Subscribe is not set")
        
        await update_group(message.chat.id, {"f_sub": None})
        await message.reply("✅ Force Subscribe removed")
        log_text = f"#FSUB_REMOVED\n\n👤 User: {message.from_user.mention}\n👥 Group: {message.chat.title}"
        await bot.send_message(LOG_CHANNEL, log_text)
        
    except Exception as e:
        logger.error(f"Remove FSub error: {e}")
        await message.reply("⚠️ An error occurred!")

@Client.on_message(filters.group & filters.command("connections"))
async def list_connections(bot, message):
    try:
        group = await get_group(message.chat.id)
        if not group:
            return
        
        if message.from_user.id != group["user_id"]:
            return await message.reply(f"⚠️ Only {group['user_name']} can do this")
        
        channels = group.get("channels", [])
        f_sub = group.get("f_sub")
        
        if not channels and not f_sub:
            return await message.reply("❌ No connections configured")
        
        response = "🔗 **Group Connections:**\n\n"
        
        for idx, channel_id in enumerate(channels, 1):
            try:
                chat = await bot.get_chat(channel_id)
                response += f"{idx}. 📢 [{chat.title}]({chat.invite_link}) `{channel_id}`\n"
            except:
                response += f"{idx}. 📢 `{channel_id}` (Invalid)\n"
        
        if f_sub:
            try:
                chat = await bot.get_chat(f_sub)
                response += f"\n🔔 **Force Subscribe:** [{chat.title}]({chat.invite_link}) `{f_sub}`"
            except:
                response += f"\n🔔 **Force Subscribe:** `{f_sub}` (Invalid)"
        
        await message.reply(response, disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Connections error: {e}")
        await message.reply("⚠️ An error occurred!")
