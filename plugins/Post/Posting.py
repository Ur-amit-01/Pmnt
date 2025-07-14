from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from plugins.helper.db import db
import time
import random
from plugins.helper.time_parser import *
import asyncio
from config import *
from plugins.Post.admin_panel import admin_filter

async def restore_pending_deletions(client):
    """Restore pending deletions when bot starts"""
    try:
        pending_posts = await db.get_pending_deletions()
        now = time.time()
        
        for post in pending_posts:
            post_id = post["post_id"]
            delete_after = post["delete_after"] - now
            
            if delete_after > 0:  # Only if deletion is in future
                channels = post.get("channels", [])
                deletion_tasks = []
                
                for channel in channels:
                    deletion_tasks.append(
                        schedule_deletion(
                            client,
                            channel["channel_id"],
                            channel["message_id"],
                            delete_after,
                            post["user_id"],
                            post_id,
                            channel.get("channel_name", str(channel["channel_id"])),
                            post.get("confirmation_msg_id")
                        )
                    )
                
                if deletion_tasks:
                    asyncio.create_task(
                        handle_deletion_results(
                            client=client,
                            deletion_tasks=deletion_tasks,
                            post_id=post_id,
                            delay_seconds=delete_after
                        )
                    )
    except Exception as e:
        print(f"Error restoring pending deletions: {e}")

@Client.on_message(filters.command(["post", "post1", "post2", "post3"]) & filters.private & admin_filter)
async def send_post(client, message: Message):
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass
    if not await db.is_admin(message.from_user.id):
        await message.reply("**❌ You are not authorized to use this command!**")
        return
    
    if not message.reply_to_message:
        await message.reply("**Reply to a message to post it.**")
        return

    # Determine which group(s) to post to based on command
    command = message.command[0].lower()
    group_numbers = []
    
    if command == "post":
        group_numbers = [0]  # Default group
    elif command == "post1":
        group_numbers = [1]
    elif command == "post2":
        group_numbers = [2]
    elif command == "post3":
        group_numbers = [3]
    
    # Also support numeric arguments like /post 1 2
    if len(message.command) > 1 and command == "post":
        try:
            group_numbers = []
            for arg in message.command[1:]:
                if arg.isdigit():
                    group_num = int(arg)
                    if 0 <= group_num <= 3:
                        group_numbers.append(group_num)
                    else:
                        await message.reply("❌ Group numbers must be between 0-3")
                        return
                else:
                    break  # Stop at first non-numeric argument (could be time spec)
            
            # If no valid group numbers found, default to group 0
            if not group_numbers:
                group_numbers = [0]
        except:
            group_numbers = [0]

    delete_after = None
    time_input = None
    
    # Parse time if provided (skip group numbers)
    time_args = []
    for arg in message.command[1:]:
        if not arg.isdigit() or int(arg) > 3:  # Not a group number
            time_args.append(arg)
    
    if time_args:
        try:
            time_input = ' '.join(time_args).lower()
            delete_after = parse_time(time_input)
            if delete_after <= 0:
                await message.reply("❌ Time must be greater than 0")
                return
        except ValueError as e:
            await message.reply(f"❌ {str(e)}\nExample: /post 1h 30min or /post 2 hours 15 minutes")
            return

    post_content = message.reply_to_message
    channels = []
    
    # Get channels from all specified groups
    for group_num in group_numbers:
        group_channels = await db.get_channels_by_group(group_num)
        channels.extend(group_channels)

    if not channels:
        group_names = ", ".join(str(g) for g in group_numbers)
        await message.reply(f"**No channels connected in group(s) {group_names} yet.**")
        return

    post_id = int(time.time())
    sent_messages = []
    success_count = 0
    total_channels = len(channels)
    failed_channels = []

    processing_msg = await message.reply(
        f"**📢 Posting to {total_channels} channels in group(s) {', '.join(str(g) for g in group_numbers)}...**",
        reply_to_message_id=post_content.id
    )

    deletion_tasks = []
    
    for channel in channels:
        try:
            sent_message = await client.copy_message(
                chat_id=channel["_id"],
                from_chat_id=message.chat.id,
                message_id=post_content.id
            )

            sent_messages.append({
                "channel_id": channel["_id"],
                "message_id": sent_message.id,
                "channel_name": channel.get("name", str(channel["_id"])),
                "group": channel.get("group", 0)
            })
            success_count += 1

            if delete_after:
                deletion_tasks.append(
                    schedule_deletion(
                        client,
                        channel["_id"],
                        sent_message.id,
                        delete_after,
                        message.from_user.id,
                        post_id,
                        channel.get("name", str(channel["_id"])),
                        processing_msg.id
                    )
                )
                
        except Exception as e:
            error_msg = str(e)[:200]  # Truncate long error messages
            print(f"Error posting to channel {channel['_id']}: {error_msg}")
            failed_channels.append({
                "channel_id": channel["_id"],
                "channel_name": channel.get("name", str(channel["_id"])),
                "error": error_msg,
                "group": channel.get("group", 0)
            })

    # Save post with deletion info if needed
    post_data = {
        "post_id": post_id,
        "channels": sent_messages,
        "user_id": message.from_user.id,
        "confirmation_msg_id": processing_msg.id,
        "created_at": time.time(),
        "groups": group_numbers
    }
    
    if delete_after:
        post_data["delete_after"] = time.time() + delete_after
        post_data["delete_original"] = True
    
    await db.save_post(post_data)

    result_msg = (
        f"<blockquote>📣 <b>Posting Completed!</b></blockquote>\n\n"
        f"• <b>Post ID:</b> <code>{post_id}</code>\n"
        f"• <b>Groups:</b> {', '.join(str(g) for g in group_numbers)}\n"
        f"• <b>Success:</b> {success_count}/{total_channels} channels\n"
    )
    
    if delete_after:
        time_str = format_time(delete_after)
        result_msg += f"• <b>Auto-delete in:</b> {time_str}\n"

    if failed_channels:
        result_msg += f"• <b>Failed:</b> {len(failed_channels)} channels\n\n"
        if len(failed_channels) <= 10:
            result_msg += "<b>Failed Channels:</b>\n"
            for idx, channel in enumerate(failed_channels, 1):
                result_msg += f"{idx}. {channel['channel_name']} (Group {channel['group']}) - {channel['error']}\n"
        else:
            result_msg += "<i>Too many failed channels to display (see logs for details)</i>\n"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 Delete This Post", callback_data=f"delete_{post_id}")]
    ])

    await processing_msg.edit_text(result_msg, reply_markup=reply_markup)

    try:
        log_msg = (
            f"📢 <blockquote><b>#Post | @Interferons_bot</b></blockquote>\n\n"
            f"👤 <b>Posted By:</b> {message.from_user.mention}\n"
            f"📌 <b>Post ID:</b> <code>{post_id}</code>\n"
            f"📡 <b>Groups:</b> {', '.join(str(g) for g in group_numbers)}\n"
            f"📡 <b>Sent to:</b> {success_count}/{total_channels} channels\n"
            f"⏳ <b>Auto-delete:</b> {time_str if delete_after else 'No'}\n"
        )
        
        if failed_channels:
            log_msg += f"\n❌ <b>Failed Channels ({len(failed_channels)}):</b>\n"
            for channel in failed_channels[:15]:
                log_msg += f"  - {channel['channel_name']} (Group {channel['group']}): {channel['error']}\n"
            if len(failed_channels) > 15:
                log_msg += f"  ...and {len(failed_channels)-15} more"
        
        await client.send_message(
            chat_id=LOG_CHANNEL,
            text=log_msg
        )    
    except Exception as e:
        print(f"Error sending confirmation to log channel: {e}")

    if delete_after and deletion_tasks:
        asyncio.create_task(
            handle_deletion_results(
                client=client,
                deletion_tasks=deletion_tasks,
                post_id=post_id,
                delay_seconds=delete_after
            )
        )

@Client.on_message(filters.command(["fpost", "fpost1", "fpost2", "fpost3"]) & filters.private & admin_filter)
async def forward_post(client, message: Message):
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass
    
    if not message.reply_to_message:
        await message.reply("**Reply to a message to forward it.**")
        return

    # Determine which group(s) to post to based on command
    command = message.command[0].lower()
    group_numbers = []
    
    if command == "fpost":
        group_numbers = [0]  # Default group
    elif command == "fpost1":
        group_numbers = [1]
    elif command == "fpost2":
        group_numbers = [2]
    elif command == "fpost3":
        group_numbers = [3]
    
    # Also support numeric arguments like /fpost 1 2
    if len(message.command) > 1 and command == "fpost":
        try:
            group_numbers = []
            for arg in message.command[1:]:
                if arg.isdigit():
                    group_num = int(arg)
                    if 0 <= group_num <= 3:
                        group_numbers.append(group_num)
                    else:
                        await message.reply("❌ Group numbers must be between 0-3")
                        return
                else:
                    break  # Stop at first non-numeric argument (could be time spec)
            
            # If no valid group numbers found, default to group 0
            if not group_numbers:
                group_numbers = [0]
        except:
            group_numbers = [0]

    delete_after = None
    time_input = None
    
    # Parse time if provided (skip group numbers)
    time_args = []
    for arg in message.command[1:]:
        if not arg.isdigit() or int(arg) > 3:  # Not a group number
            time_args.append(arg)
    
    if time_args:
        try:
            time_input = ' '.join(time_args).lower()
            delete_after = parse_time(time_input)
            if delete_after <= 0:
                await message.reply("❌ Time must be greater than 0")
                return
        except ValueError as e:
            await message.reply(f"❌ {str(e)}\nExample: /fpost 1h 30min or /fpost 2 hours 15 minutes")
            return

    post_content = message.reply_to_message
    channels = []
    
    # Get channels from all specified groups
    for group_num in group_numbers:
        group_channels = await db.get_channels_by_group(group_num)
        channels.extend(group_channels)

    if not channels:
        group_names = ", ".join(str(g) for g in group_numbers)
        await message.reply(f"**No channels connected in group(s) {group_names} yet.**")
        return

    post_id = int(time.time())
    sent_messages = []
    success_count = 0
    total_channels = len(channels)
    failed_channels = []

    processing_msg = await message.reply(
        f"**📢 Forwarding to {total_channels} channels in group(s) {', '.join(str(g) for g in group_numbers)}...**",
        reply_to_message_id=post_content.id
    )

    deletion_tasks = []
    
    for channel in channels:
        try:
            sent_message = await client.forward_messages(
                chat_id=channel["_id"],
                from_chat_id=message.chat.id,
                message_ids=post_content.id
            )

            sent_messages.append({
                "channel_id": channel["_id"],
                "message_id": sent_message.id,
                "channel_name": channel.get("name", str(channel["_id"])),
                "group": channel.get("group", 0)
            })
            success_count += 1

            if delete_after:
                deletion_tasks.append(
                    schedule_deletion(
                        client,
                        channel["_id"],
                        sent_message.id,
                        delete_after,
                        message.from_user.id,
                        post_id,
                        channel.get("name", str(channel["_id"])),
                        processing_msg.id
                    )
                )
                
        except Exception as e:
            error_msg = str(e)[:200]  # Truncate long error messages
            print(f"Error forwarding to channel {channel['_id']}: {error_msg}")
            failed_channels.append({
                "channel_id": channel["_id"],
                "channel_name": channel.get("name", str(channel["_id"])),
                "error": error_msg,
                "group": channel.get("group", 0)
            })

    post_data = {
        "post_id": post_id,
        "channels": sent_messages,
        "user_id": message.from_user.id,
        "confirmation_msg_id": processing_msg.id,
        "created_at": time.time(),
        "is_forward": True,
        "groups": group_numbers
    }
    
    if delete_after:
        post_data["delete_after"] = time.time() + delete_after
        post_data["delete_original"] = True
    
    await db.save_post(post_data)

    result_msg = (
        f"<blockquote>📣 <b>Forwarding Completed!</b></blockquote>\n\n"
        f"• <b>Post ID:</b> <code>{post_id}</code>\n"
        f"• <b>Groups:</b> {', '.join(str(g) for g in group_numbers)}\n"
        f"• <b>Success:</b> {success_count}/{total_channels} channels\n"
    )
    
    if delete_after:
        time_str = format_time(delete_after)
        result_msg += f"• <b>Auto-delete in:</b> {time_str}\n"

    if failed_channels:
        result_msg += f"• <b>Failed:</b> {len(failed_channels)} channels\n\n"
        if len(failed_channels) <= 10:
            result_msg += "<b>Failed Channels:</b>\n"
            for idx, channel in enumerate(failed_channels, 1):
                result_msg += f"{idx}. {channel['channel_name']} (Group {channel['group']}) - {channel['error']}\n"
        else:
            result_msg += "<i>Too many failed channels to display (see logs for details)</i>\n"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 Delete This Post", callback_data=f"delete_{post_id}")]
    ])

    await processing_msg.edit_text(result_msg, reply_markup=reply_markup)

    try:
        log_msg = (
            f"📢 <blockquote><b>#FPost | @Interferons_bot</b></blockquote>\n\n"
            f"👤 <b>Forwarded By:</b> {message.from_user.mention}\n"
            f"📌 <b>Post ID:</b> <code>{post_id}</code>\n"
            f"📡 <b>Groups:</b> {', '.join(str(g) for g in group_numbers)}\n"
            f"📡 <b>Sent to:</b> {success_count}/{total_channels} channels\n"
            f"⏳ <b>Auto-delete:</b> {time_str if delete_after else 'No'}\n"
        )
        
        if failed_channels:
            log_msg += f"\n❌ <b>Failed Channels ({len(failed_channels)}):</b>\n"
            for channel in failed_channels[:15]:
                log_msg += f"  - {channel['channel_name']} (Group {channel['group']}): {channel['error']}\n"
            if len(failed_channels) > 15:
                log_msg += f"  ...and {len(failed_channels)-15} more"
        
        await client.send_message(
            chat_id=LOG_CHANNEL,
            text=log_msg
        )    
    except Exception as e:
        print(f"Error sending confirmation to log channel: {e}")

    if delete_after and deletion_tasks:
        asyncio.create_task(
            handle_deletion_results(
                client=client,
                deletion_tasks=deletion_tasks,
                post_id=post_id,
                delay_seconds=delete_after
            )
		) 
