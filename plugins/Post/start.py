from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, BotCommand, CallbackQuery
from config import *
from plugins.helper.db import db
import asyncio
from datetime import datetime, timedelta
import random
import pytz  
IST = pytz.timezone("Asia/Kolkata")

# NEET Exam Date - 30th April 2026
NEET_DATE = datetime(2026, 4, 30)
BOT_USERNAME = "Neet_countdown_robot"  # Change this to your bot's username

# Store group settings
group_settings = {}

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

    txt = (
        f"👋 **Hey {message.from_user.mention}!**\n\n"
        "**I'm NEET 2026 Countdown Bot** ⏰\n\n"
        "• Track days left for NEET 2026\n"
        "• Motivational messages\n"
    )
    
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton('📚 Add to Group', url=f'https://t.me/{BOT_USERNAME}?startgroup=true'),
        InlineKeyboardButton('ℹ️ Help', callback_data='help')]
    ])

    if START_PIC:
        await message.reply_photo(START_PIC, caption=txt, reply_markup=button)
    else:
        await message.reply_text(text=txt, reply_markup=button)


@Client.on_message(filters.command("days"))
async def days_command(client: Client, message: Message):
    """Show days left for NEET 2026"""
    days_left = await get_days_left()
    
    countdown_text = await get_countdown_message(days_left)
    
    # Try to edit existing countdown message if exists
    chat_id = message.chat.id
    if chat_id in group_settings and 'countdown_msg_id' in group_settings[chat_id]:
        try:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=group_settings[chat_id]['countdown_msg_id'],
                text=countdown_text
            )
            await message.delete()
            return
        except:
            pass
    
    # Send new countdown message
    countdown_msg = await message.reply_text(countdown_text)
    
    # Store message ID for future updates
    if chat_id not in group_settings:
        group_settings[chat_id] = {}
    group_settings[chat_id]['countdown_msg_id'] = countdown_msg.id
    group_settings[chat_id]['last_update'] = datetime.now()
    
    await message.delete()


@Client.on_callback_query(filters.regex("help"))
async def help_handler(client: Client, callback_query: CallbackQuery):
    """Show help message"""
    help_text = (
        "**NEET Countdown Bot Help** 📚\n\n"
        "**Commands:**\n"
        "• /start - Start the bot\n"
        "• /days - Show days left for NEET\n"
        "• /auto - Enable auto countdown (Admins)\n"
        "**Features:**\n"
        "• Daily countdown updates\n"
        "• Study planner\n"
        "• Motivational quotes\n"
        "• Automatic reminders\n\n"
        "**Add me to your NEET preparation group!**"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton('📚 Add to Group', url=f'https://t.me/{BOT_USERNAME}?startgroup=true')],
        [InlineKeyboardButton('🔙 Back', callback_data='back_start')]
    ])
    
    if callback_query.message.photo:
        await callback_query.message.delete()
        await callback_query.message.reply_text(help_text, reply_markup=buttons)
    else:
        await callback_query.message.edit_text(help_text, reply_markup=buttons)


@Client.on_callback_query(filters.regex("back_start"))
async def back_start(client: Client, callback_query: CallbackQuery):
    """Go back to start"""
    await start(client, callback_query.message)


@Client.on_message(filters.private & filters.command("stats"))
async def stats_command(client: Client, message: Message):
    """Show bot statistics"""
    total_users = await db.total_users_count()
    total_groups = len(group_settings)
    
    days_left = await get_days_left()
    
    stats_text = (
        "**📊 NEET Countdown Bot Stats**\n\n"
        f"**👥 Total Users:** {total_users}\n"
        f"**👥 Groups Using:** {total_groups}\n"
        f"**⏰ Days Left:** {days_left} days\n"
        f"**🎯 Exam Date:** 30th April 2026\n\n"
        "**Keep Studying! 💪**"
    )
    
    await message.reply_text(stats_text)


async def get_days_left():
    """Calculate days left until NEET 2026"""
    today = datetime.now(IST).date()
    neet_date = NEET_DATE.date()
    delta = neet_date - today
    return delta.days


async def get_countdown_message(days_left):
    """Generate countdown message with motivational quote"""
    quotes = [
        "**Every hour you study today is an hour closer to your dream college!** 🏥",
        "**Consistency is the key to cracking NEET!** 🔑",
        "**Your future self will thank you for studying today!** 🙏",
        "**Small daily improvements lead to stunning results!** ⭐",
        "**Don't watch the clock; do what it does. Keep going!** ⏰",
        "**The pain of studying is temporary, but the pride of success is permanent!** 🎯"
    ]
    
    
    countdown_text = (
        f">**⏰ NEET 2026 COUNTDOWN**\n\n"
        f"**📅 Exam Date: 30th April 2026**\n"
        f"**⏳ Days Left: {days_left} days left**\n\n"
        f">**{random.choice(quotes)}**"
    )
    
    return countdown_text
    

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast_handler(client: Client, message: Message):
    """Broadcast message to all users (Admin only)"""
    if not message.reply_to_message:
        await message.reply_text("Please reply to a message to broadcast.")
        return
    
    users = await db.get_all_users()
    success = 0
    failed = 0
    
    for user in users:
        try:
            await message.reply_to_message.copy(user['user_id'])
            success += 1
        except:
            failed += 1
        await asyncio.sleep(0.1)  # Prevent flooding
    
    await message.reply_text(f"Broadcast completed!\nSuccess: {success}\nFailed: {failed}")


# Start background task when bot starts
@Client.on_message(filters.command("init"))
async def init_bot(client: Client, message: Message):
    """Initialize background tasks"""
    asyncio.create_task(send_daily_countdown(client))
    await message.reply_text("✅ Background tasks started!")


# =====================================================================================
# Set bot commands
@Client.on_message(filters.command("setcommands"))
async def set_commands(client: Client, message: Message):
    await client.set_bot_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("days", "Check days left for NEET"),
        BotCommand("auto", "Enable auto countdown (Admins)")
    ])
    await message.reply_text("✅ Bot commands updated!")


@Client.on_message(filters.command("id"))
async def id_command(client: Client, message: Message):
    chat_id = message.chat.id
    await message.reply_text(f"**Chat ID:** `{chat_id}`")
