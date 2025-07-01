import traceback
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    ApiIdInvalid, PhoneNumberInvalid, PhoneCodeInvalid,
    PhoneCodeExpired, SessionPasswordNeeded, PasswordHashInvalid,
    FloodWait, UserNotParticipant
)
from info import API_ID, API_HASH, DATABASE_URI, ADMIN
from pymongo import MongoClient

# Initialize MongoDB
mongo_client = MongoClient(DATABASE_URI)
db = mongo_client.userdb
sessions_collection = db.sessions

# Constants
SESSION_STRING_SIZE = 351
LOGIN_TIMEOUT = 600  # 10 minutes
MAX_LOGIN_ATTEMPTS = 3
LOGIN_COOLDOWN = 300  # 5 minutes

# Security validation
def validate_phone_number(number):
    """Validate phone number format"""
    if not number.startswith('+'):
        return False
    clean_number = number[1:].replace(' ', '')
    return clean_number.isdigit() and 7 <= len(clean_number) <= 15

# Login state tracker
login_attempts = {}

@Client.on_message(filters.private & filters.command(["logout"]) & filters.user(ADMIN))
async def logout_handler(_, msg: Message):
    """Handle user logout"""
    user_data = sessions_collection.find_one({"chat_id": msg.chat.id})
    
    if not user_data or not user_data.get('session'):
        return await msg.reply("❌ You're not currently logged in")
    
    sessions_collection.update_one(
        {"_id": user_data['_id']},
        {"$set": {'session': None, 'logged_in': False}}
    )
    
    # Reset login attempts
    if msg.chat.id in login_attempts:
        del login_attempts[msg.chat.id]
    
    await msg.reply("✅ **Logout Successful**\n\nYour session has been securely removed")

@Client.on_message(filters.private & filters.command(["session"]) & filters.user(ADMIN))
async def session_status(_, msg: Message):
    """Show login status"""
    user_data = sessions_collection.find_one({"chat_id": msg.chat.id})
    
    if user_data and user_data.get('logged_in'):
        status = "🟢 **Logged In**"
        created = user_data.get('login_time', 'Unknown')
    else:
        status = "🔴 **Not Logged In**"
        created = "N/A"
    
    await msg.reply(
        f"**Account Status:**\n\n"
        f"{status}\n"
        f"**Login Time:** `{created}`\n\n"
        "Use /login to authenticate\n"
        "Use /logout to remove session"
    )

@Client.on_message(filters.private & filters.command(["login"]) & filters.user(ADMIN))
async def login_handler(bot: Client, msg: Message):
    """Handle user login process"""
    user_id = msg.from_user.id
    
    # Check login attempts
    attempts = login_attempts.get(user_id, 0)
    if attempts >= MAX_LOGIN_ATTEMPTS:
        await msg.reply(
            f"⛔ **Too many failed attempts!**\n\n"
            f"Please wait {LOGIN_COOLDOWN//60} minutes before trying again"
        )
        return
    
    # Check if already logged in
    user_data = sessions_collection.find_one({"chat_id": user_id})
    if user_data and user_data.get('logged_in'):
        await msg.reply(
            "⚠️ **You're already logged in!**\n\n"
            "Use /logout first if you want to login with a different account"
        )
        return
    
    # Start login process
    cancel_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Cancel Login", callback_data="cancel_login")]
    ])
    
    phone_msg = await bot.send_message(
        user_id,
        "📱 **Enter your phone number with country code**\n\n"
        "Example: `+14155552671` or `+918123456789`\n\n"
        "🔐 *We don't store your number*",
        reply_markup=cancel_keyboard
    )
    
    try:
        phone_number_msg = await bot.listen(
            user_id, 
            filters=filters.text, 
            timeout=120
        )
    except asyncio.TimeoutError:
        await phone_msg.edit("⏱️ **Login timed out**. Please restart with /login")
        return
    
    if phone_number_msg.text.startswith('/'):
        await phone_number_msg.reply("❌ Login cancelled")
        return
    
    # Validate phone number
    if not validate_phone_number(phone_number_msg.text):
        await phone_number_msg.reply(
            "❌ **Invalid phone number format!**\n\n"
            "Please use international format: `+[country code][number]`\n"
            "Example: `+14155552671` for US, `+918123456789` for India"
        )
        login_attempts[user_id] = attempts + 1
        return
    
    phone_number = phone_number_msg.text
    
    # Create temporary client
    temp_client = Client(
        name=f"temp_session_{user_id}",
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True
    )
    
    try:
        await temp_client.connect()
        
        # Send OTP
        sent_msg = await phone_number_msg.reply("🔒 **Sending OTP...**")
        code = await temp_client.send_code(phone_number)
        
        # Get OTP from user
        otp_msg = await bot.send_message(
            user_id,
            "✉️ **Enter the OTP sent to your Telegram account**\n\n"
            "Format: `1 2 3 4 5` (with spaces between digits)\n\n"
            "⚠️ OTP expires in 10 minutes",
            reply_markup=cancel_keyboard
        )
        
        try:
            otp_response = await bot.listen(
                user_id, 
                filters=filters.text, 
                timeout=LOGIN_TIMEOUT
            )
        except asyncio.TimeoutError:
            await otp_msg.edit("⏱️ **OTP timed out**. Please restart with /login")
            return
        
        if otp_response.text.startswith('/'):
            await otp_response.reply("❌ Login cancelled")
            return
        
        # Process OTP
        phone_code = otp_response.text.replace(" ", "")
        
        try:
            await temp_client.sign_in(
                phone_number, 
                code.phone_code_hash, 
                phone_code
            )
        except (PhoneCodeInvalid, PhoneCodeExpired):
            await otp_response.reply("❌ **Invalid or expired OTP!** Please restart with /login")
            login_attempts[user_id] = attempts + 1
            return
        except SessionPasswordNeeded:
            # Handle 2FA
            password_msg = await bot.send_message(
                user_id,
                "🔐 **Two-Step Verification Enabled**\n\n"
                "Please enter your account password:",
                reply_markup=cancel_keyboard
            )
            
            try:
                password_response = await bot.listen(
                    user_id, 
                    filters=filters.text, 
                    timeout=300
                )
            except asyncio.TimeoutError:
                await password_msg.edit("⏱️ **Password entry timed out**. Please restart with /login")
                return
            
            if password_response.text.startswith('/'):
                await password_response.reply("❌ Login cancelled")
                return
            
            try:
                await temp_client.check_password(password_response.text)
            except PasswordHashInvalid:
                await password_response.reply("❌ **Invalid password!** Please restart with /login")
                login_attempts[user_id] = attempts + 1
                return
        
        # Successfully logged in
        string_session = await temp_client.export_session_string()
        
        if len(string_session) < SESSION_STRING_SIZE:
            await msg.reply("❌ **Invalid session generated!** Please try again")
            return
        
        # Save session to database
        session_data = {
            "session": string_session,
            "logged_in": True,
            "login_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "phone_number": phone_number  # Stored for reference only
        }
        
        if user_data:
            sessions_collection.update_one(
                {"_id": user_data['_id']},
                {"$set": session_data}
            )
        else:
            session_data["chat_id"] = user_id
            sessions_collection.insert_one(session_data)
        
        # Reset login attempts
        if user_id in login_attempts:
            del login_attempts[user_id]
        
        # Send success message
        await msg.reply(
            "✅ **Login Successful!**\n\n"
            "Your session has been securely stored\n\n"
            "⚠️ **Security Notice:**\n"
            "- Never share your session string\n"
            "- Use /logout when accessing from new devices\n"
            "- Enable 2FA on your Telegram account"
        )
        
    except (PhoneNumberInvalid, ApiIdInvalid):
        await phone_number_msg.reply("❌ **Invalid API credentials or phone number!** Contact admin")
    except FloodWait as e:
        await phone_number_msg.reply(
            f"⏳ **Too many attempts!** Please wait {e.value} seconds before trying again"
        )
    except Exception as e:
        error_trace = traceback.format_exc()
        await msg.reply(f"❌ **Critical Error:** `{str(e)}`\n\nContact admin immediately!")
        # Log full error to admin
        await bot.send_message(
            ADMIN,
            f"⚠️ **Login Error**\n\nUser: {msg.from_user.mention}\nError:```{error_trace}```"
        )
    finally:
        await temp_client.disconnect()

@Client.on_callback_query(filters.regex("^cancel_login$"))
async def cancel_login_callback(_, query):
    """Handle login cancellation"""
    await query.message.edit("❌ **Login Cancelled**")
    await query.answer()
