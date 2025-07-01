from utils import *
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton 
from pyrogram.errors import FloodWait, UserNotParticipant
import asyncio
import time

# Cache bot info to reduce API calls
bot_info_cache = {}
last_cache_refresh = 0
CACHE_TTL = 3600  # 1 hour

async def get_bot_info(bot):
    """Get bot info with caching"""
    global bot_info_cache, last_cache_refresh
    
    current_time = time.time()
    if current_time - last_cache_refresh > CACHE_TTL or not bot_info_cache:
        bot_info_cache = await bot.get_me()
        last_cache_refresh = current_time
    
    return bot_info_cache

def create_start_buttons(bot_username):
    """Generate consistent button layout for start messages"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                '➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ➕', 
                url=f'https://t.me/{bot_username}?startgroup=true'
            )
        ],
        [
            InlineKeyboardButton("ʜᴇʟᴘ", callback_data="misc_help"),
            InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="misc_about")
        ],
        [
            InlineKeyboardButton("🤖 ᴜᴘᴅᴀᴛᴇ", url="https://t.me/rmcbackup"),
            InlineKeyboardButton("🔍 ɢʀᴏᴜᴘ", url="https://t.me/rmcmovierequest")
        ]
    ])

@Client.on_message(filters.command("start") & filters.private)
async def start_command(bot, message):
    """Handle /start command in private chats"""
    try:
        # Add user to database
        await add_user(message.from_user.id, message.from_user.first_name)
        
        # Get bot info
        bot_info = await get_bot_info(bot)
        
        # Send welcome message
        await message.reply(
            text=script.START.format(message.from_user.mention, bot_info.username),
            disable_web_page_preview=True,
            reply_markup=create_start_buttons(bot_info.username)
        )
        
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        await start_command(bot, message)
    except Exception as e:
        logging.error(f"Start command error: {str(e)}")

@Client.on_message(filters.command("help") & filters.private)
async def help_command(bot, message):
    """Handle /help command"""
    try:
        await message.reply(
            text=script.HELP, 
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="misc_home")]
            ])
        )
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        await help_command(bot, message)

@Client.on_message(filters.command("about") & filters.private)
async def about_command(bot, message):
    """Handle /about command"""
    try:
        bot_info = await get_bot_info(bot)
        await message.reply(
            text=script.ABOUT.format(bot_info.mention), 
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="misc_home")]
            ])
        )
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        await about_command(bot, message)

@Client.on_message(filters.command("stats") & filters.user(ADMIN))
async def stats_command(bot, message):
    """Handle /stats command for admins"""
    try:
        u_count = await total_users_count()
        g_count = await total_chat_count()
        await message.reply(script.STATS.format(u_count, g_count))
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@Client.on_message(filters.command("id"))
async def id_command(bot, message):
    """Handle /id command"""
    try:
        text = f"**Chat ID:** `{message.chat.id}`\n"
        
        if message.from_user:
            text += f"**Your ID:** `{message.from_user.id}`\n"
        
        if message.reply_to_message:
            replied = message.reply_to_message
            if replied.from_user:
                text += f"**Replied User ID:** `{replied.from_user.id}`\n"
            if replied.forward_from:
                text += f"**Forwarded User ID:** `{replied.forward_from.id}`\n"
            if replied.forward_from_chat:
                text += f"**Forwarded Chat ID:** `{replied.forward_from_chat.id}`\n"
            if replied.forward_sender_name:
                text += f"**Forward Sender Name:** {replied.forward_sender_name}\n"
        
        await message.reply(text)
        
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        await id_command(bot, message)

@Client.on_callback_query(filters.regex(r"^misc_"))
async def misc_callback(bot, update):
    """Handle misc callback queries"""
    try:
        action = update.data.split("_")[-1]
        bot_info = await get_bot_info(bot)
        
        if action == "home":
            await update.message.edit(
                text=script.START.format(update.from_user.mention, bot_info.username),
                disable_web_page_preview=True,
                reply_markup=create_start_buttons(bot_info.username)
            )
            
        elif action == "help":
            await update.message.edit(
                text=script.HELP,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back", callback_data="misc_home")]
                ])
            )
            
        elif action == "about":
            await update.message.edit(
                text=script.ABOUT.format(bot_info.mention),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back", callback_data="misc_home")]
                ])
            )
            
        await update.answer()
        
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        await misc_callback(bot, update)
    except Exception as e:
        logging.error(f"Callback error: {str(e)}")
