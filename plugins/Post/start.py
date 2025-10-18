from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message, BotCommand
from config import *
from plugins.helper.db import db
import random

# Store payment requests temporarily (in production, use database)
payment_requests = {}

# =====================================================================================

@Client.on_message(filters.private & filters.command("start"))
async def start(client, message: Message):
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass

    # Add user to database
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id)
        total_users = await db.total_users_count()
        await client.send_message(LOG_CHANNEL, LOG_TEXT.format(message.from_user.mention, message.from_user.id, total_users))

    # Simple welcome message
    txt = (
        f"👋 **Hey {message.from_user.mention}!**\n\n"
        "**Get 150k+ Premium Reels Bundle** 🎬\n\n"
        "• Ready-to-use templates\n"
        "• All categories included\n"
        "• Instant delivery\n\n"
        "**Only ₹199** 💰"
    )
    
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton('💳 Buy Now - ₹199', callback_data='pay')],
        [InlineKeyboardButton('❓ How it works', callback_data='help')]
    ])

    if START_PIC:
        await message.reply_photo(START_PIC, caption=txt, reply_markup=button)
    else:
        await message.reply_text(text=txt, reply_markup=button)


@Client.on_message(filters.private & filters.command("pay"))
async def pay_command(client: Client, message: Message):
    await send_payment(client, message)


@Client.on_callback_query(filters.regex("pay"))
async def pay_callback(client: Client, callback_query: CallbackQuery):
    await send_payment(client, callback_query)


async def send_payment(client, update):
    """Simple payment message"""
    payment_text = (
        "**💳 Payment - ₹199**\n\n"
        "**150k+ Reels Bundle**\n\n"
        "1. Pay ₹199 using QR code\n"
        "2. Click 'I Paid' and send screenshot\n"
        "3. Get instant access after verification\n\n"
        "Need help? Contact @alphaeditorssquad"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Paid", callback_data="paid")],
        [InlineKeyboardButton("📞 Support", url="https://t.me/alphaeditorssquad")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])
    
    try:
        if isinstance(update, CallbackQuery):
            await update.message.delete()
            await update.message.reply_photo("payment.jpg", caption=payment_text, reply_markup=buttons)
        else:
            await update.reply_photo("payment.jpg", caption=payment_text, reply_markup=buttons)
    except:
        # If no QR image
        if isinstance(update, CallbackQuery):
            await update.message.edit_text(payment_text + "\n\n⚠️ QR code missing, contact support", reply_markup=buttons)
        else:
            await update.reply_text(payment_text + "\n\n⚠️ QR code missing, contact support", reply_markup=buttons)


@Client.on_callback_query(filters.regex("paid"))
async def paid_handler(client: Client, callback_query: CallbackQuery):
    """Ask for payment screenshot"""
    text = (
        "**📸 Please send your payment screenshot**\n\n"
        "1. Take a screenshot of your payment confirmation\n"
        "2. Send it here\n"
        "3. We'll verify and send your PDF immediately\n\n"
        "**Note:** Make sure transaction ID is visible"
    )
    
    # Set user in waiting for screenshot state
    user_id = callback_query.from_user.id
    payment_requests[user_id] = {
        "username": callback_query.from_user.username,
        "first_name": callback_query.from_user.first_name,
        "status": "waiting_screenshot"
    }
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Cancel", callback_data="pay")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=buttons)
    await callback_query.answer("Please send your payment screenshot now")


@Client.on_message(filters.private & (filters.photo | filters.document))
async def handle_screenshot(client: Client, message: Message):
    """Handle payment screenshot"""
    user_id = message.from_user.id
    
    # Check if user is waiting to send screenshot
    if user_id not in payment_requests or payment_requests[user_id]["status"] != "waiting_screenshot":
        return
    
    # Update status
    payment_requests[user_id]["status"] = "pending_approval"
    payment_requests[user_id]["screenshot_message_id"] = message.id
    
    # Notify user
    await message.reply_text(
        "✅ **Screenshot received!**\n\n"
        "We're verifying your payment. You'll get the PDF within 5-10 minutes.\n\n"
        "Status: ⏳ Pending Approval"
    )
    
    # Send to log channel for approval
    log_text = (
        "**🔄 New Payment Verification Request**\n\n"
        f"**User:** {message.from_user.mention}\n"
        f"**User ID:** `{user_id}`\n"
        f"**Username:** @{message.from_user.username}\n"
        f"**Name:** {message.from_user.first_name}\n\n"
        "**Action Required:** Verify payment and approve/reject"
    )
    
    approve_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
        ]
    ])
    
    # Forward screenshot to log channel
    if message.photo:
        await client.send_photo(
            LOG_CHANNEL,
            message.photo.file_id,
            caption=log_text,
            reply_markup=approve_buttons
        )
    else:
        await client.send_document(
            LOG_CHANNEL,
            message.document.file_id,
            caption=log_text,
            reply_markup=approve_buttons
        )


@Client.on_callback_query(filters.regex(r"approve_(\d+)"))
async def approve_payment(client: Client, callback_query: CallbackQuery):
    """Admin approves payment - forwards the PDF post to user"""
    user_id = int(callback_query.matches[0].group(1))
    
    if user_id not in payment_requests:
        await callback_query.answer("User not found", show_alert=True)
        return
    
    try:
        # Forward the PDF post to user (message 210 from chat 2835704997)
        await client.forward_messages(
            chat_id=user_id,
            from_chat_id=-1002835704997,  # Convert to supergroup format
            message_ids=210
        )
        
        # Send confirmation message
        success_text = (
            "**🎉 Payment Verified! Thank you for your purchase!**\n\n"
            "**📦 Your 150k+ Reels Bundle has been sent!**\n\n"
            "**What's Next:**\n"
            "• Check the PDF above for download links\n"
            "• Save the PDF for future reference\n"
            "• Start creating amazing content! 🎬\n\n"
            "Need help? Contact @alphaeditorssquad\n\n"
            "**Happy Creating! 💫**"
        )
        
        await client.send_message(user_id, success_text)
        
        # Update status
        payment_requests[user_id]["status"] = "approved"
        
        # Update log message
        admin_name = callback_query.from_user.first_name
        await callback_query.message.edit_caption(
            f"✅ **APPROVED**\n\n{callback_query.message.caption}\n\n"
            f"**Status:** Approved by {admin_name}\n"
            f"**Time:** {callback_query.message.date}\n"
            f"**PDF Sent:** ✅ Yes"
        )
        
        await callback_query.answer("Payment approved! PDF forwarded to user.")
        
    except Exception as e:
        error_msg = f"Error forwarding PDF: {str(e)}"
        await callback_query.answer(error_msg, show_alert=True)


@Client.on_callback_query(filters.regex(r"reject_(\d+)"))
async def reject_payment(client: Client, callback_query: CallbackQuery):
    """Admin rejects payment - asks user to send screenshot again"""
    user_id = int(callback_query.matches[0].group(1))
    
    if user_id not in payment_requests:
        await callback_query.answer("User not found", show_alert=True)
        return
    
    try:
        # Reset user status so they can send screenshot again
        payment_requests[user_id]["status"] = "waiting_screenshot"
        
        # Notify user with specific rejection reason
        rejection_text = (
            "**❌ Payment Verification Failed**\n\n"
            "We couldn't verify your payment. Possible issues:\n\n"
            "• **Screenshot is blurry/unclear** 📸\n"
            "• **Transaction ID not visible** 🔍\n"
            "• **Wrong amount paid** 💰\n"
            "• **Payment not received** ⚠️\n\n"
            "**Please send a clear payment screenshot again:**\n"
            "1. Make sure transaction ID is visible\n"
            "2. Ensure amount ₹199 is shown\n"
            "3. Take a clear, full-screen screenshot\n\n"
            "If problem continues, contact @alphaeditorssquad"
        )
        
        retry_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("📸 Send Screenshot Again", callback_data="paid")],
            [InlineKeyboardButton("📞 Contact Support", url="https://t.me/alphaeditorssquad")]
        ])
        
        await client.send_message(
            user_id,
            rejection_text,
            reply_markup=retry_button
        )
        
        # Update log message
        admin_name = callback_query.from_user.first_name
        await callback_query.message.edit_caption(
            f"❌ **REJECTED**\n\n{callback_query.message.caption}\n\n"
            f"**Status:** Rejected by {admin_name}\n"
            f"**Time:** {callback_query.message.date}\n"
            f"**Action:** User asked to resend screenshot"
        )
        
        await callback_query.answer("Payment rejected! User notified to resend screenshot.")
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)


@Client.on_callback_query(filters.regex("help"))
async def help_handler(client: Client, callback_query: CallbackQuery):
    """Simple help"""
    text = (
        "**How to Get Started:**\n\n"
        "1. Click **'Buy Now'**\n"
        "2. Pay **₹199** via QR code\n"
        "3. Send payment screenshot\n"
        "4. Get instant access after verification\n\n"
        "That's it! Simple and fast. 🚀"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Buy Now - ₹199", callback_data="pay")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=buttons)


@Client.on_callback_query(filters.regex("back"))
async def back_handler(client: Client, callback_query: CallbackQuery):
    """Go back to start"""
    await start(client, callback_query.message)


@Client.on_message(filters.command("id"))
async def id_command(client: Client, message: Message):
    chat_title = message.chat.title or message.from_user.full_name
    id_text = f"**Chat ID of {chat_title}:**\n`{message.chat.id}`"
    await message.reply_text(id_text)


# =====================================================================================
# Set bot commands
@Client.on_message(filters.command("set") & admin_filter)
async def set_commands(client: Client, message: Message):
    await client.set_bot_commands([
        BotCommand("start", "Start bot"),
        BotCommand("pay", "Buy Reels Bundle - ₹199"),
        BotCommand("id", "Get chat ID"),
    ])
    await message.reply_text("✅ Bot commands updated")
