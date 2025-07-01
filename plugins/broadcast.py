import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

@Client.on_message(filters.command('broadcast') & filters.user(ADMIN))
async def user_broadcast(bot, message):
    if not message.reply_to_message:
        return await message.reply("Use this command as a reply to any message!")
    
    m = await message.reply("⚡ Starting user broadcast...")
    users = await get_users()
    total = len(users)
    success = failed = 0

    for index, user in enumerate(users):
        try:
            await message.reply_to_message.copy(user["_id"])
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value + 2)
            await message.reply_to_message.copy(user["_id"])
            success += 1
        except Exception:
            await delete_user(user["_id"])
            failed += 1
        
        if index % 100 == 0 or index == total - 1:
            await m.edit(script.BROADCAST.format(
                "IN PROGRESS", 
                total, 
                total - index - 1,
                success,
                failed
            ))
    
    await m.edit(script.BROADCAST.format(
        "USER BROADCAST COMPLETED", 
        total, 
        0,
        success,
        failed
    ))

@Client.on_message(filters.command('broadcast_groups') & filters.user(ADMIN))
async def group_broadcast(bot, message):
    if not message.reply_to_message:
        return await message.reply("Use this command as a reply to any message!")
    
    m = await message.reply("⚡ Starting group broadcast...")
    groups = await get_groups()
    total = len(groups)
    success = failed = 0

    for index, group in enumerate(groups):
        try:
            msg = await message.reply_to_message.copy(group["_id"])
            await msg.pin(disable_notification=True)
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value + 2)
            msg = await message.reply_to_message.copy(group["_id"])
            await msg.pin(disable_notification=True)
            success += 1
        except Exception:
            await delete_group(group["_id"])
            failed += 1
        
        if index % 50 == 0 or index == total - 1:
            await m.edit(script.BROADCAST.format(
                "IN PROGRESS", 
                total, 
                total - index - 1,
                success,
                failed
            ))
    
    await m.edit(script.BROADCAST.format(
        "GROUP BROADCAST COMPLETED", 
        total, 
        0,
        success,
        failed
    ))
