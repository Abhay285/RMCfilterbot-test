import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_group, update_group
from utils.script import script
from info import LOG_CHANNEL

logger = logging.getLogger(__name__)

@Client.on_message(filters.group & filters.command("verify"))
async def verify_group(bot, message):
    try:
        group = await get_group(message.chat.id)
        if not group:
            await bot.leave_chat(message.chat.id)
            return
        
        admin_id = group["user_id"]
        admin_name = group["user_name"]
        is_verified = group.get("verified", False)
        
        # Check if already verified
        if is_verified:
            return await message.reply(script.ABOUT.format("This group is already verified!"))
        
        # Verify command sender
        if message.from_user.id != admin_id:
            return await message.reply(
                f"⚠️ Only {admin_name} can verify this group!"
            )
        
        # Get group invite link
        try:
            chat = await bot.get_chat(message.chat.id)
            invite_link = chat.invite_link
            if not invite_link:
                # Create invite link if not available
                invite_link = (await bot.create_chat_invite_link(
                    message.chat.id, creates_join_request=True
                )).invite_link
        except Exception:
            return await message.reply(
                "❌ I need 'Invite Users' permission to generate links!"
            )
        
        # Prepare verification request
        request_text = (
            f"#VERIFICATION_REQUEST\n\n"
            f"👤 User: {message.from_user.mention} ({message.from_user.id})\n"
            f"👥 Group: [{chat.title}]({invite_link}) ({message.chat.id})\n"
            f"👥 Members: {chat.members_count}"
        )
        
        # Send to log channel
        await bot.send_message(
            LOG_CHANNEL,
            request_text,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"verify_approve_{message.chat.id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"verify_reject_{message.chat.id}")
                ],
                [
                    InlineKeyboardButton("👁️ View Group", url=invite_link)
                ]
            ])
        )
        
        # Send confirmation
        await message.reply("🔒 Verification request sent! You'll be notified when approved.")
        
    except Exception as e:
        logger.error(f"Verify error: {str(e)}")
        await message.reply("⚠️ An error occurred!")

@Client.on_callback_query(filters.regex(r"^verify_(approve|reject)_"))
async def verify_callback(bot, update):
    try:
        action = update.data.split("_")[1]
        group_id = int(update.data.split("_")[-1])
        
        group = await get_group(group_id)
        if not group:
            await update.answer("❌ Group not found!")
            return
            
        if action == "approve":
            # Approve verification
            await update_group(group_id, {"verified": True})
            await bot.send_message(
                group["user_id"],
                f"✅ Your group {group['name']} has been verified!"
            )
            await update.message.edit(
                f"#APPROVED ✅\n\nGroup: {group['name']}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Approved", callback_data="verified")]
                ])
            )
            await update.answer("Group approved!")
        else:
            # Reject verification
            await delete_group(group_id)
            await bot.send_message(
                group["user_id"],
                f"❌ Your group {group['name']} was rejected!"
            )
            await update.message.edit(
                f"#REJECTED ❌\n\nGroup: {group['name']}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Rejected", callback_data="rejected")]
                ])
            )
            await update.answer("Group rejected!")
            
    except Exception as e:
        logger.error(f"Verify callback error: {str(e)}")
        await update.answer("⚠️ Error occurred!", show_alert=True)
