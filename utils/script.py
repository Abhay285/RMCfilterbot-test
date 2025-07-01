# utils/script.py
START_TEXT = """
👋 Hello {mention},

I'm a powerful filter + search bot. I can help you manage and search posts across connected channels.

Use /help to see what I can do!
"""

HELP_TEXT = """
🛠 **Bot Commands:**

/start - Check if I'm alive
/id - Get Channel/Group/User ID
/verify - Verify group connection
/connect - Connect to a channel
/disconnect - Remove connection
/fsub - Set force subscribe channel
/nofsub - Remove force subscribe
/stats - Get usage stats
/broadcast - Send message to all users
/login - Owner login
/logout - Logout session
/user - User details
/userc - User count
/connections - List connected channels
/help - Show this help message
"""

VERIFY_MESSAGE = "✅ Group verified successfully!"
NOT_SUBSCRIBED = "🔒 Please join our channel to use this bot."
TRY_AGAIN_BTN = "✅ Joined, Try Again"
JOIN_MESSAGE = "You need to join [this channel](https://t.me/{}) to use the bot."

INVALID_COMMAND = "⚠️ Invalid command. Use /help to see available options."
LOG_TEXT = "👤 User: `{}`\n🔍 Query: `{}`\n🕒 Time: `{}`"
