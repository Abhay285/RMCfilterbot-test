import logging
import asyncio
from pyrogram import Client, filters
from utils.Helpers import get_users, get_groups
from utils.Script import script
from info import ADMIN

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("broadcast") & filters.user(ADMIN))
async def broadcast_users(bot, message):
    try:
        if not message.reply_to_message:
            return await message.reply("❌ Reply to a message to broadcast")
        
        m = await message.reply("⚡ Broadcasting...")
        
        users = await get_users()
        total = len(users)
        success = 0
        
        for user in users:
            try:
                await message.reply_to_message.copy(user["_id"])
                success += 1
            except Exception as e:
                logger.error(f"Broadcast to {user['_id']} failed: {str(e)}")
            
            # Update progress
            if total > 0 and (success % 10 == 0 or success == total):
                await m.edit(script.BROADCAST.format(
                    "IN PROGRESS", 
                    total, 
                    total - success,
                    success,
                    total - success
                ))
        
        # Final report
        await m.edit(script.BROADCAST.format(
            "COMPLETED", 
            total, 
            0,
            success,
            total - success
        ))
        
    except Exception as e:
        logger.error(f"Broadcast error: {str(e)}")
        await message.reply("⚠️ Broadcast failed!")

@Client.on_message(filters.command("broadcast_groups") & filters.user(ADMIN))
async def broadcast_groups(bot, message):
    try:
        if not message.reply_to_message:
            return await message.reply("❌ Reply to a message to broadcast")
        
        m = await message.reply("⚡ Broadcasting to groups...")
        
        groups = await get_groups()
        total = len(groups)
        success = 0
        
        for group in groups:
            try:
                await message.reply_to_message.copy(group["_id"])
                success += 1
            except Exception as e:
                logger.error(f"Broadcast to {group['_id']} failed: {str(e)}")
            
            # Update progress
            if total > 0 and (success % 5 == 0 or success == total):
                await m.edit(script.BROADCAST.format(
                    "IN PROGRESS", 
                    total, 
                    total - success,
                    success,
                    total - success
                ))
        
        # Final report
        await m.edit(script.BROADCAST.format(
            "COMPLETED", 
            total, 
            0,
            success,
            total - success
        ))
        
    except Exception as e:
        logger.error(f"Group broadcast error: {str(e)}")
        await message.reply("⚠️ Broadcast failed!")
