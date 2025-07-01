import logging
from pyrogram import Client, filters
from utils.Helpers import add_user
from utils.Script import script

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("start") & filters.private)
async def start_command(bot, message):
    try:
        await add_user(message.from_user.id, message.from_user.first_name)
        await message.reply(
            script.START.format(message.from_user.mention),
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Start error: {str(e)}")

@Client.on_message(filters.command("help"))
async def help_command(bot, message):
    try:
        await message.reply(
            script.HELP,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Help error: {str(e)}")

@Client.on_message(filters.command("about"))
async def about_command(bot, message):
    try:
        me = await bot.get_me()
        await message.reply(
            script.ABOUT.format(me.mention),
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"About error: {str(e)}")

@Client.on_message(filters.command("stats") & filters.user(ADMIN))
async def stats_command(bot, message):
    try:
        users = await total_users_count()
        groups = await total_chat_count()
        await message.reply(script.STATS.format(users, groups))
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        await message.reply("⚠️ Error getting stats")

@Client.on_message(filters.command("id"))
async def id_command(bot, message):
    try:
        text = f"**Chat ID:** `{message.chat.id}`\n"
        if message.from_user:
            text += f"**Your ID:** `{message.from_user.id}`\n"
        if message.reply_to_message:
            replied = message.reply_to_message
            if replied.from_user:
                text += f"**Replied User ID:** `{replied.from_user.id}`\n"
        await message.reply(text)
    except Exception as e:
        logger.error(f"ID error: {str(e)}")
        await message.reply("⚠️ Error getting IDs")
