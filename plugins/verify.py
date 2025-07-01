from info import *
from utils import *
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, PeerIdInvalid

@Client.on_message(filters.group & filters.command("verify"))
async def handle_verification_request(bot, message):
    """Handle group verification requests"""
    try:
        # Get group data
        group = await get_group(message.chat.id)
        if not group:
            await message.reply("❌ Group not registered! Adding me again might fix this.")
            return
        
        admin_id = group["user_id"]
        admin_name = group["user_name"]
        is_verified = group.get("verified", False)
        
        # Check if already verified
        if is_verified:
            return await message.reply("✅ **This group is already verified!**")
        
        # Verify command sender
        if message.from_user.id != admin_id:
            return await message.reply(
                f"⚠️ **Only {admin_name} can verify this group!**\n\n"
                "The group owner must use this command."
            )
        
        # Get group invite link
        try:
            chat = await bot.get_chat(message.chat.id)
            invite_link = chat.invite_link
            if not invite_link:
                # Try to create invite link if not available
                invite_link = (await bot.create_chat_invite_link(
                    message.chat.id, creates_join_request=True
                )).invite_link
        except (ChatAdminRequired, PeerIdInvalid):
            return await message.reply(
                "❌ **Admin Privilege Required!**\n\n"
                "I need 'Invite Users' permission to generate invite links."
            )
        
        # Prepare verification request
        request_text = (
            f"#VERIFICATION_REQUEST\n\n"
            f"👤 **User:** {message.from_user.mention} (`{message.from_user.id}`)\n"
            f"👥 **Group:** [{chat.title}]({invite_link}) (`{message.chat.id}`)\n"
            f"👥 **Members:** `{chat.members_count}`\n\n"
            f"🕒 **Request Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Send to log channel with approval buttons
        await bot.send_message(
            chat_id=LOG_CHANNEL,
            text=request_text,
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
        
        # Send confirmation to group
        await message.reply(
            "🔒 **Verification Request Submitted!**\n\n"
            "Our team will review your group shortly. You'll receive a notification "
            "once it's approved. This usually takes less than 24 hours.\n\n"
            f"⏱️ Request ID: `{message.chat.id}`"
        )
        
    except Exception as e:
        logging.error(f"Verification error: {str(e)}")
        await message.reply("⚠️ An error occurred. Please try again or contact support.")

@Client.on_callback_query(filters.regex(r"^verify_(approve|reject)_"))
async def handle_verification_response(bot, update):
    """Handle verification approval/rejection from admin"""
    try:
        # Extract data from callback
        action = update.data.split("_")[1]
        group_id = int(update.data.split("_")[-1])
        
        # Get group data
        group = await get_group(group_id)
        if not group:
            await update.answer("❌ Group not found in database!")
            return await update.message.edit("⚠️ Group not found in database!")
        
        admin_id = group["user_id"]
        group_name = group["group_name"]
        
        # Update message based on action
        if action == "approve":
            # Approve verification
            await update_group(group_id, {"verified": True})
            
            # Notify group admin
            await bot.send_message(
                admin_id,
                f"🎉 **Group Verified!**\n\n"
                f"Your group **{group_name}** has been approved!\n\n"
                "You can now use all bot features:"
                "\n• /connect - Link channels"
                "\n• /fsub - Setup force subscribe"
                "\n• /settings - Configure group"
            )
            
            # Update log message
            new_text = update.message.text.replace(
                "#VERIFICATION_REQUEST", 
                "#VERIFIED ✅"
            )
            await update.message.edit(
                new_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Approved", callback_data="verified")],
                    [InlineKeyboardButton("👁️ View Group", url=update.message.reply_markup.inline_keyboard[2][0].url)]
                ])
            )
            await update.answer("✅ Group approved!")
            
        else:  # Reject action
            # Notify group admin
            await bot.send_message(
                admin_id,
                f"❌ **Verification Rejected**\n\n"
                f"Your group **{group_name}** was not approved.\n\n"
                "Possible reasons:"
                "\n• Group doesn't meet requirements"
                "\n• Suspicious activity detected"
                "\n• Incomplete application"
                "\n\nContact @AdminUsername for more details."
            )
            
            # Update log message
            new_text = update.message.text.replace(
                "#VERIFICATION_REQUEST", 
                "#REJECTED ❌"
            )
            await update.message.edit(
                new_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Rejected", callback_data="rejected")],
                    [InlineKeyboardButton("👁️ View Group", url=update.message.reply_markup.inline_keyboard[2][0].url)]
                ])
            )
            await update.answer("❌ Group rejected!")
            
    except Exception as e:
        logging.error(f"Verification response error: {str(e)}")
        await update.answer("⚠️ An error occurred!", show_alert=True)
