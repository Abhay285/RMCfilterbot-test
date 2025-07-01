import logging
import traceback
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import (
    ApiIdInvalid, PhoneNumberInvalid, PhoneCodeInvalid,
    PhoneCodeExpired, SessionPasswordNeeded, PasswordHashInvalid
)
from info import API_ID, API_HASH, ADMIN
from utils.Helpers import database

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("login") & filters.user(ADMIN))
async def login_handler(bot, message):
    try:
        # Check if already logged in
        user_data = database.find_one({"chat_id": ADMIN})
        if user_data and user_data.get('logged_in'):
            return await message.reply("⚠️ You're already logged in! Use /logout first")
        
        # Start login process
        phone_msg = await bot.ask(
            message.chat.id,
            "📱 Enter your phone number (with country code):",
            filters=filters.text
        )
        phone_number = phone_msg.text
        
        # Create temporary client
        temp_client = Client(
            "temp_session", 
            api_id=API_ID, 
            api_hash=API_HASH, 
            in_memory=True
        )
        await temp_client.connect()
        
        # Send OTP
        sent_code = await temp_client.send_code(phone_number)
        otp_msg = await bot.ask(
            message.chat.id,
            "✉️ Enter the OTP you received (format: 1 2 3 4 5):",
            filters=filters.text
        )
        phone_code = otp_msg.text.replace(" ", "")
        
        try:
            # Sign in
            await temp_client.sign_in(
                phone_number, 
                sent_code.phone_code_hash, 
                phone_code
            )
        except SessionPasswordNeeded:
            # Handle 2FA
            password_msg = await bot.ask(
                message.chat.id,
                "🔑 Enter your 2FA password:",
                filters=filters.text
            )
            await temp_client.check_password(password_msg.text)
        
        # Export session string
        session_string = await temp_client.export_session_string()
        
        # Save to database
        database.update_one(
            {"chat_id": ADMIN},
            {"$set": {"session": session_string, "logged_in": True}},
            upsert=True
        )
        
        await message.reply("✅ Login successful! Session saved")
        await temp_client.disconnect()
        
    except (PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired, PasswordHashInvalid) as e:
        await message.reply(f"❌ Error: {str(e)}")
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        await message.reply("⚠️ An error occurred during login")

@Client.on_message(filters.command("logout") & filters.user(ADMIN))
async def logout_handler(bot, message):
    try:
        database.update_one(
            {"chat_id": ADMIN},
            {"$set": {"session": None, "logged_in": False}}
        )
        await message.reply("✅ Logout successful! Session removed")
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        await message.reply("⚠️ Error during logout")
