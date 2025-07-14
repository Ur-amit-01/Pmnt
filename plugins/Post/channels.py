from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from plugins.helper.db import db
import time
import random
import asyncio
from config import *
from plugins.Post.admin_panel import admin_filter

async def add_channel_to_group(client, message: Message, group_number=0):
    channel_id = message.chat.id
    channel_name = message.chat.title

    try:
        added = await db.add_channel(channel_id, channel_name, group_number)
        if added:
            await message.reply(f"**Channel '{channel_name}' added to group {group_number}! ✅**")
        else:
            await message.reply(f"ℹ️ Channel '{channel_name}' already exists in group {group_number}.")
    except Exception as e:
        print(f"Error adding channel: {e}")
        await message.reply("❌ Failed to add channel. Contact developer.")

async def remove_channel_from_group(client, message: Message, group_number=0):
    channel_id = message.chat.id
    channel_name = message.chat.title

    try:
        if await db.is_channel_exist(channel_id, group_number):
            await db.delete_channel(channel_id, group_number)
            await message.reply(f"**Channel '{channel_name}' removed from group {group_number}!**")
        else:
            await message.reply(f"ℹ️ Channel '{channel_name}' not found in group {group_number}.")
    except Exception as e:
        print(f"Error removing channel: {e}")
        await message.reply("❌ Failed to remove channel. Try again.")

# Command to add the current channel to different groups
@Client.on_message(filters.command("add") & filters.channel)
async def add_current_channel_group0(client, message: Message):
    await add_channel_to_group(client, message, 0)

@Client.on_message(filters.command("add1") & filters.channel)
async def add_current_channel_group1(client, message: Message):
    await add_channel_to_group(client, message, 1)

@Client.on_message(filters.command("add2") & filters.channel)
async def add_current_channel_group2(client, message: Message):
    await add_channel_to_group(client, message, 2)

@Client.on_message(filters.command("add3") & filters.channel)
async def add_current_channel_group3(client, message: Message):
    await add_channel_to_group(client, message, 3)

# Command to remove the current channel from different groups
@Client.on_message(filters.command("rem") & filters.channel)
async def remove_current_channel_group0(client, message: Message):
    await remove_channel_from_group(client, message, 0)

@Client.on_message(filters.command("rem1") & filters.channel)
async def remove_current_channel_group1(client, message: Message):
    await remove_channel_from_group(client, message, 1)

@Client.on_message(filters.command("rem2") & filters.channel)
async def remove_current_channel_group2(client, message: Message):
    await remove_channel_from_group(client, message, 2)

@Client.on_message(filters.command("rem3") & filters.channel)
async def remove_current_channel_group3(client, message: Message):
    await remove_channel_from_group(client, message, 3)

# Command to list all connected channels in specific groups
@Client.on_message(filters.command("channels") & filters.private & admin_filter)
async def list_channels_group0(client, message: Message):
    await list_channels_by_group(client, message, 0)

@Client.on_message(filters.command("channels1") & filters.private & admin_filter)
async def list_channels_group1(client, message: Message):
    await list_channels_by_group(client, message, 1)

@Client.on_message(filters.command("channels2") & filters.private & admin_filter)
async def list_channels_group2(client, message: Message):
    await list_channels_by_group(client, message, 2)

@Client.on_message(filters.command("channels3") & filters.private & admin_filter)
async def list_channels_group3(client, message: Message):
    await list_channels_by_group(client, message, 3)

async def list_channels_by_group(client, message: Message, group_number=0):
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass
    
    if not await db.is_admin(message.from_user.id):
        await message.reply("**❌ You are not authorized to use this command!**")
        return
    
    channels = await db.get_all_channels(group_number)

    if not channels:
        await message.reply(f"**No channels connected in group {group_number} yet.🙁**")
        return

    total_channels = len(channels)
    channel_list = [f"• **{channel['name']}** :- `{channel['_id']}`" for channel in channels]

    header = f"> **Total Channels in Group {group_number} :- ({total_channels})**\n\n"
    messages = []
    current_message = header

    for line in channel_list:
        if len(current_message) + len(line) + 1 > 4096:
            messages.append(current_message)
            current_message = ""
        current_message += line + "\n"

    if current_message:
        messages.append(current_message)

    for part in messages:
        await message.reply(part)
