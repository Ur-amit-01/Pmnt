from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message, BotCommand
from config import *
from plugins.helper.db import db
import random

# Store payment requests temporarily
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

    # Clean welcome message
    txt = (
        f"👋 **Hey {message.from_user.mention}!**\n\n"
        "**150k+ Premium Reels Bundle** 🎬\n\n"
        "• All Categories Included\n"
        "• Instant Delivery\n"
        "• Only ₹199\n\n"
        "Click **Buy Now** to get started!"
    )
    
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton('💳 Buy Now - ₹199', callback_data='pay')],
        [InlineKeyboardButton('❓ Help', callback_data='help')]
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
    """Show QR code and payment instructions"""
    payment_text = (
        "**💳 Get Your Reels Bundle**\n\n"
        "**Price:** ₹199\n\n"
        "**To Pay:**\n"
        "1. Scan the QR code below\n"
        "2. Pay ₹199\n"
        "3. Click **'I Paid'**\n"
        "4. Send payment screenshot\n\n"
        "Need help? Contact @alphaeditorssquad"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Paid", callback_data="paid")],
        [InlineKeyboardButton("❓ Help", callback_data="help")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])
    
    # Show QR code image
    try:
        if isinstance(update, CallbackQuery):
            await update.message.delete()
            await update.message.reply_photo("payment.jpg", caption=payment_text, reply_markup=buttons)
        else:
            await update.reply_photo("payment.jpg", caption=payment_text, reply_markup=buttons)
    except Exception as e:
        # If QR code image is not found
        error_text = payment_text + "\n\n⚠️ **QR Code not available. Please contact @alphaeditorssquad for payment details.**"
        if isinstance(update, CallbackQuery):
            await update.message.edit_text(error_text, reply_markup=buttons)
        else:
            await update.reply_text(error_text, reply_markup=buttons)


@Client.on_callback_query(filters.regex("paid"))
async def paid_handler(client: Client, callback_query: CallbackQuery):
    """Ask for payment screenshot - No QR code shown"""
    text = (
        "**📸 Send Payment Screenshot**\n\n"
        "Please send your payment confirmation screenshot.\n\n"
        "**Make sure:**\n"
        "• Transaction ID is visible\n"
        "• Amount ₹199 is shown\n"
        "• Screenshot is clear"
    )
    
    # Set user in waiting for screenshot state
    user_id = callback_query.from_user.id
    payment_requests[user_id] = {
        "username": callback_query.from_user.username,
        "first_name": callback_query.from_user.first_name,
        "status": "waiting_screenshot",
        "pending_message_id": callback_query.message.id  # Store message to delete later
    }
    
    # Delete the previous payment message (with QR code)
    try:
        await callback_query.message.delete()
    except:
        pass
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="pay")]
    ])
    
    # Send new message asking for screenshot (NO QR CODE)
    new_message = await callback_query.message.reply_text(text, reply_markup=buttons)
    payment_requests[user_id]["screenshot_request_id"] = new_message.id
    
    await callback_query.answer("Please send your payment screenshot")


@Client.on_message(filters.private & (filters.photo | filters.document))
async def handle_screenshot(client: Client, message: Message):
    """Handle payment screenshot"""
    user_id = message.from_user.id
    
    # Check if user is waiting to send screenshot
    if user_id not in payment_requests or payment_requests[user_id]["status"] != "waiting_screenshot":
        return
    
    # Delete the screenshot request message
    try:
        await client.delete_messages(
            message.chat.id, 
            payment_requests[user_id]["screenshot_request_id"]
        )
    except:
        pass
    
    # Update status
    payment_requests[user_id]["status"] = "pending_approval"
    payment_requests[user_id]["screenshot_message_id"] = message.id
    
    # Clean confirmation message
    confirm_msg = await message.reply_text(
        "✅ **Screenshot Received**\n\n"
        "We're verifying your payment.\n"
        "You'll get access in 5-10 minutes.\n\n"
        "Status: ⏳ **Pending Approval**"
    )
    
    payment_requests[user_id]["pending_message_id"] = confirm_msg.id
    
    # Send to log channel for approval
    log_text = (
        "**🔄 Payment Verification**\n\n"
        f"**User:** {message.from_user.mention}\n"
        f"**ID:** `{user_id}`\n"
        f"**Username:** @{message.from_user.username}\n\n"
        "**Action:** Verify and click below"
    )
    
    approve_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
        ]
    ])
    
    # Forward screenshot to log channel
    if message.photo:
        log_msg = await client.send_photo(
            LOG_CHANNEL,
            message.photo.file_id,
            caption=log_text,
            reply_markup=approve_buttons
        )
    else:
        log_msg = await client.send_document(
            LOG_CHANNEL,
            message.document.file_id,
            caption=log_text,
            reply_markup=approve_buttons
        )
    
    payment_requests[user_id]["log_message_id"] = log_msg.id


@Client.on_callback_query(filters.regex(r"approve_(\d+)"))
async def approve_payment(client: Client, callback_query: CallbackQuery):
    """Admin approves payment - copy PDF without forward tag"""
    user_id = int(callback_query.matches[0].group(1))
    
    if user_id not in payment_requests:
        await callback_query.answer("User not found", show_alert=True)
        return
    
    try:
        # Delete user's pending message
        try:
            await client.delete_messages(
                user_id, 
                payment_requests[user_id]["pending_message_id"]
            )
        except:
            pass
        
        # Copy the PDF post (no forward tag)
        await client.copy_message(
            chat_id=user_id,
            from_chat_id=-1002835704997,  # Your channel
            message_id=210  # Your PDF post
        )
        
        # Clean success message
        success_text = (
            "**🎉 Payment Verified!**\n\n"
            "**Your Reels Bundle is ready!** 🎬\n\n"
            "Check the PDF above for download links.\n"
            "Start creating amazing content!\n\n"
            "Need help? Contact @alphaeditorssquad"
        )
        
        await client.send_message(user_id, success_text)
        
        # Update status
        payment_requests[user_id]["status"] = "approved"
        
        # Update log message
        await callback_query.message.edit_caption(
            f"✅ **APPROVED**\n\n"
            f"User: {payment_requests[user_id]['first_name']}\n"
            f"ID: `{user_id}`\n"
            f"By: {callback_query.from_user.first_name}\n"
            f"PDF: ✅ Sent"
        )
        
        await callback_query.answer("Approved! User got PDF")
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)


@Client.on_callback_query(filters.regex(r"reject_(\d+)"))
async def reject_payment(client: Client, callback_query: CallbackQuery):
    """Admin rejects payment - clean rejection"""
    user_id = int(callback_query.matches[0].group(1))
    
    if user_id not in payment_requests:
        await callback_query.answer("User not found", show_alert=True)
        return
    
    try:
        # Delete user's pending message
        try:
            await client.delete_messages(
                user_id, 
                payment_requests[user_id]["pending_message_id"]
            )
        except:
            pass
        
        # Reset user status
        payment_requests[user_id]["status"] = "rejected"
        
        # Clean rejection message
        rejection_text = (
            "**❌ Payment Not Verified**\n\n"
            "We couldn't verify your payment.\n\n"
            "**Please check:**\n"
            "• Screenshot is clear\n"
            "• Transaction ID visible\n"
            "• Amount is ₹199\n\n"
            "Click below to try again:"
        )
        
        retry_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Try Again", callback_data="paid")],
            [InlineKeyboardButton("📞 Contact Support", url="https://t.me/alphaeditorssquad")]
        ])
        
        await client.send_message(
            user_id,
            rejection_text,
            reply_markup=retry_button
        )
        
        # Update log message
        await callback_query.message.edit_caption(
            f"❌ **REJECTED**\n\n"
            f"User: {payment_requests[user_id]['first_name']}\n"
            f"ID: `{user_id}`\n"
            f"By: {callback_query.from_user.first_name}\n"
            f"Status: User asked to retry"
        )
        
        await callback_query.answer("Rejected! User notified")
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)


@Client.on_callback_query(filters.regex("help"))
async def help_handler(client: Client, callback_query: CallbackQuery):
    """Clean help message"""
    text = (
        "**How It Works:**\n\n"
        "1. **Buy Now** - Click to start\n"
        "2. **Pay ₹199** - Scan QR code\n"
        "3. **Send Screenshot** - Payment proof\n"
        "4. **Get Access** - Instant delivery\n\n"
        "Simple & Fast! 🚀"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Buy Now", callback_data="pay")],
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
    id_text = f"**Chat ID:** `{message.chat.id}`"
    await message.reply_text(id_text)


# =====================================================================================
# Set bot commands
@Client.on_message(filters.command("set"))
async def set_commands(client: Client, message: Message):
    await client.set_bot_commands([
        BotCommand("start", "Start bot"),
        BotCommand("pay", "Buy Reels Bundle - ₹199"),
        BotCommand("id", "Get chat ID"),
    ])
    await message.reply_text("✅ Bot commands updated")
