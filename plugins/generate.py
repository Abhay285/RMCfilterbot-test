import logging
from pyrogram import Client, filters
from pyrogram.errors import (
    PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid
)
from info import API_ID, API_HASH, ADMIN
from plugins.database import database

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("login") & filters.user(ADMIN))
async def login_handler(bot, message):
    try:
        user_data = await database.find_user(ADMIN)
        if user_data and user_data.get('session'):
            return await message.reply("⚠️ You're already logged in! Use /logout first")
        
        phone_msg = await bot.ask(message.chat.id, "📱 Enter your phone number (with country code):", filters=filters.text)
        phone_number = phone_msg.text
        
        temp_client = Client("temp_session", api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await temp_client.connect()
        
        try:
            sent_code = await temp_client.send_code(phone_number)
        except PhoneNumberInvalid:
            return await message.reply("❌ Invalid phone number")
        
        otp_msg = await bot.ask(message.chat.id, "✉️ Enter the OTP (format: 1 2 3 4 5):", filters=filters.text)
        phone_code = otp_msg.text.replace(" ", "")
        
        try:
            await temp_client.sign_in(phone_number, sent_code.phone_code_hash, phone_code)
        except PhoneCodeInvalid:
            return await message.reply("❌ Invalid OTP")
        except PhoneCodeExpired:
            return await message.reply("❌ OTP expired")
        except SessionPasswordNeeded:
            password_msg = await bot.ask(message.chat.id, "🔑 Enter your 2FA password:", filters=filters.text)
            try:
                await temp_client.check_password(password_msg.text)
            except PasswordHashInvalid:
                return await message.reply("❌ Invalid password")
        
        session_string = await temp_client.export_session_string()
        await database.update_user(ADMIN, {"session": session_string})
        
        await message.reply("✅ Login successful! Session saved")
        await temp_client.disconnect()
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        await message.reply("⚠️ Login failed!")

@Client.on_message(filters.command("logout") & filters.user(ADMIN))
async def logout_handler(bot, message):
    try:
        await database.update_user(ADMIN, {"session": None})
        await message.reply("✅ Logout successful! Session removed")
    except Exception as e:
        logger.error(f"Logout error: {e}")
        await message.reply("⚠️ Logout failed")
