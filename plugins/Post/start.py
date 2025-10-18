from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message, BotCommand
from config import *
from plugins.helper.db import db
import random


# =====================================================================================

@Client.on_message(filters.private & filters.command("start"))
async def start(client, message: Message):
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)  # React with a random emoji
    except:
        pass

    # Add user to the database if they don't exist
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id)
        total_users = await db.total_users_count()
        await client.send_message(LOG_CHANNEL, LOG_TEXT.format(message.from_user.mention, message.from_user.id, total_users))

    # Welcome message
    txt = (
        f"> **✨👋🏻 Hey {message.from_user.mention} !!**\n\n"
        f"**Welcome to the Channel Manager Bot, Manage multiple channels and post messages with ease! 😌**\n\n"
    )
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton('📜 ᴀʙᴏᴜᴛ', callback_data='about'), InlineKeyboardButton('🕵🏻‍♀️ ʜᴇʟᴘ', callback_data='help')]
    ])

    # Send the start message with or without a picture
    if START_PIC:
        await message.reply_photo(START_PIC, caption=txt, reply_markup=button)
    else:
        await message.reply_text(text=txt, reply_markup=button, disable_web_page_preview=True)


@Client.on_message(filters.command("id"))
async def id_command(client: Client, message: Message):
    if message.chat.title:
        chat_title = message.chat.title
    else:
        chat_title = message.from_user.full_name

    id_text = f"**Chat ID of** {chat_title} **is**\n`{message.chat.id}`"

    await client.send_message(
        chat_id=message.chat.id,
        text=id_text,
        reply_to_message_id=message.id,
    )


@Client.on_message(filters.private & filters.command("pay"))
async def pay_command(client: Client, message: Message):
    """
    Handle /pay command - Send QR code for payment
    """
    try:
        # Payment details message
        payment_text = (
            "**💳 Payment Details**\n\n"
            "**Product:** 150k+ Mega Reels Bundle\n"
            "**Price:** ₹199\n\n"
            "**Payment Instructions:**\n"
            "1. Scan the QR code below to pay ₹199\n"
            "2. After payment, forward the payment receipt to @alphaeditorssquad\n"
            "3. You'll receive your download links within 24 hours\n\n"
            "**Payment Methods Accepted:**\n"
            "• UPI (Google Pay, PhonePe, Paytm)\n"
            "• Bank Transfer\n\n"
            "**Need Help?** Contact @alphaeditorssquad"
        )
        
        # Create buttons for additional actions
        payment_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Contact Support", url="https://t.me/alphaeditorssquad")],
            [InlineKeyboardButton("✅ I've Paid", callback_data="paid_confirmation")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ])
        
        # Send QR code image with payment details
        try:
            await message.reply_photo(
                photo="payment.jpg",  # Make sure this file is in your repository
                caption=payment_text,
                reply_markup=payment_buttons
            )
        except Exception as e:
            # If QR code image is not found, send text only
            error_text = payment_text + "\n\n⚠️ *QR Code temporarily unavailable. Please contact @alphaeditorssquad for manual payment instructions.*"
            await message.reply_text(
                text=error_text,
                reply_markup=payment_buttons,
                disable_web_page_preview=True
            )
            
    except Exception as e:
        await message.reply_text("❌ Error processing payment request. Please try again later.")


@Client.on_callback_query(filters.regex("paid_confirmation"))
async def paid_confirmation(client: Client, callback_query: CallbackQuery):
    """
    Handle paid confirmation callback
    """
    confirmation_text = (
        "**✅ Payment Confirmation Received**\n\n"
        "Thank you for your payment! Please follow these steps:\n\n"
        "1. **Forward your payment receipt** to @alphaeditorssquad\n"
        "2. **Include your Telegram username** in the message\n"
        "3. **Wait for verification** (usually within 24 hours)\n"
        "4. **You'll receive** download links once verified\n\n"
        "For urgent queries, contact @alphaeditorssquad directly."
    )
    
    await callback_query.message.edit_text(
        text=confirmation_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Contact Support", url="https://t.me/alphaeditorssquad")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_pay")]
        ])
    )


@Client.on_callback_query(filters.regex("back_to_pay"))
async def back_to_pay(client: Client, callback_query: CallbackQuery):
    """
    Go back to payment screen
    """
    payment_text = (
        "**💳 Payment Details**\n\n"
        "**Product:** 150k+ Mega Reels Bundle\n"
        "**Price:** ₹199\n\n"
        "**Payment Instructions:**\n"
        "1. Scan the QR code below to pay ₹199\n"
        "2. After payment, forward the payment receipt to @alphaeditorssquad\n"
        "3. You'll receive your download links within 24 hours\n\n"
        "**Payment Methods Accepted:**\n"
        "• UPI (Google Pay, PhonePe, Paytm)\n"
        "• Bank Transfer\n\n"
        "**Need Help?** Contact @alphaeditorssquad"
    )
    
    payment_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Contact Support", url="https://t.me/alphaeditorssquad")],
        [InlineKeyboardButton("✅ I've Paid", callback_data="paid_confirmation")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
    ])
    
    try:
        await callback_query.message.edit_media(
            media=InputMediaPhoto("payment.jpg"),
            reply_markup=payment_buttons
        )
        await callback_query.message.edit_caption(
            caption=payment_text,
            reply_markup=payment_buttons
        )
    except:
        await callback_query.message.edit_text(
            text=payment_text + "\n\n⚠️ *QR Code temporarily unavailable. Please contact @alphaeditorssquad for manual payment instructions.*",
            reply_markup=payment_buttons,
            disable_web_page_preview=True
        )


@Client.on_callback_query(filters.regex("main_menu"))
async def main_menu(client: Client, callback_query: CallbackQuery):
    """
    Return to main menu
    """
    txt = (
        f"> **✨👋🏻 Hey {callback_query.from_user.mention} !!**\n\n"
        f"**Welcome to the Channel Manager Bot, Manage multiple channels and post messages with ease! 😌**\n\n"
    )
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton('📜 ᴀʙᴏᴜᴛ', callback_data='about'), InlineKeyboardButton('🕵🏻‍♀️ ʜᴇʟᴘ', callback_data='help')]
    ])
    
    await callback_query.message.edit_text(
        text=txt,
        reply_markup=button,
        disable_web_page_preview=True
    )


# =====================================================================================
# Set bot commands
@Client.on_message(filters.command("set") & admin_filter)
async def set_commands(client: Client, message: Message):
    await client.set_bot_commands([
        BotCommand("start", "🤖 ꜱᴛᴀʀᴛ ᴍᴇ"),
        BotCommand("channels", "📋 ʟɪꜱᴛ ᴏꜰ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴄʜᴀɴɴᴇʟꜱ"),
        BotCommand("admin", "🛠️ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ"),
        BotCommand("post", "📢 ꜱᴇɴᴅ ᴘᴏꜱᴛ"),
        BotCommand("fpost", "📢 sᴇɴᴅ ᴘᴏsᴛ ᴡɪᴛʜ ғᴏʀᴡᴀʀᴅ ᴛᴀɢ"),
        BotCommand("del_post", "🗑️ ᴅᴇʟᴇᴛᴇ ᴘᴏꜱᴛ"),
        BotCommand("add", "➕ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ"),
        BotCommand("rem", "➖ ʀᴇᴍᴏᴠᴇ ᴄʜᴀɴɴᴇʟ"),
        BotCommand("pay", "💳 Pay for Reels Bundle"),  # New command added
    ])
    await message.reply_text("✅ Bot commands have been set.")
