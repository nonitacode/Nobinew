from pyrogram import filters
from pyrogram.types import Message, CallbackQuery

from AnonXMusic import YouTube, app
from AnonXMusic.core.call import Anony
from AnonXMusic.misc import db
from AnonXMusic.utils import AdminRightsCheck, seconds_to_min
from AnonXMusic.utils.decorators.admins import ActualAdminCB
from AnonXMusic.utils.inline import close_markup
from AnonXMusic.utils.inline.play import stream_markup_timer
from config import BANNED_USERS


@app.on_message(
    filters.command(["seek", "cseek", "seekback", "cseekback"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def seek_comm(cli, message: Message, _, chat_id):
    if len(message.command) == 1:
        return await message.reply_text(_["admin_20"])
    query = message.text.split(None, 1)[1].strip()
    if not query.isnumeric():
        return await message.reply_text(_["admin_21"])
    playing = db.get(chat_id)
    if not playing:
        return await message.reply_text(_["queue_2"])
    duration_seconds = int(playing[0]["seconds"])
    if duration_seconds == 0:
        return await message.reply_text(_["admin_22"])
    file_path = playing[0]["file"]
    duration_played = int(playing[0]["played"])
    duration_to_skip = int(query)
    duration = playing[0]["dur"]
    if message.command[0][-2] == "c":
        if (duration_played - duration_to_skip) <= 10:
            return await message.reply_text(
                text=_["admin_23"].format(seconds_to_min(duration_played), duration),
                reply_markup=close_markup(_),
            )
        to_seek = duration_played - duration_to_skip + 1
    else:
        if (duration_seconds - (duration_played + duration_to_skip)) <= 10:
            return await message.reply_text(
                text=_["admin_23"].format(seconds_to_min(duration_played), duration),
                reply_markup=close_markup(_),
            )
        to_seek = duration_played + duration_to_skip + 1
    mystic = await message.reply_text(_["admin_24"])
    if "vid_" in file_path:
        n, file_path = await YouTube.video(playing[0]["vidid"], True)
        if n == 0:
            return await message.reply_text(_["admin_22"])
    check = (playing[0]).get("speed_path")
    if check:
        file_path = check
    if "index_" in file_path:
        file_path = playing[0]["vidid"]
    try:
        await Anony.seek_stream(
            chat_id,
            file_path,
            seconds_to_min(to_seek),
            duration,
            playing[0]["streamtype"],
        )
    except:
        return await mystic.edit_text(_["admin_26"], reply_markup=close_markup(_))
    if message.command[0][-2] == "c":
        db[chat_id][0]["played"] -= duration_to_skip
    else:
        db[chat_id][0]["played"] += duration_to_skip
    await mystic.edit_text(
        text=_["admin_25"].format(seconds_to_min(to_seek), message.from_user.mention),
        reply_markup=close_markup(_),
    )


# Inline button callback handlers for seek functionality
@app.on_callback_query(filters.regex("seek") & ~BANNED_USERS)
@ActualAdminCB
async def seek_callback(cli, callback_query: CallbackQuery, _):
    """Handle seek button callbacks"""
    callback_data = callback_query.data
    chat_id = callback_query.message.chat.id
    
    try:
        # Parse callback data: "seek chat_id seconds" or "seekback chat_id seconds"
        parts = callback_data.split()
        if len(parts) != 3:
            return await callback_query.answer("❌ Invalid callback data!", show_alert=True)
        
        command = parts[0]
        seconds = int(parts[2])
        is_backward = command == "seekback"
        
        await handle_seek_inline(callback_query, chat_id, seconds, is_backward, _)
        
    except ValueError:
        await callback_query.answer("❌ Invalid seek value!", show_alert=True)
    except Exception as e:
        await callback_query.answer("❌ Seek operation failed!", show_alert=True)


@app.on_callback_query(filters.regex("seekback") & ~BANNED_USERS)
@ActualAdminCB
async def seekback_callback(cli, callback_query: CallbackQuery, _):
    """Handle seekback button callbacks"""
    callback_data = callback_query.data
    chat_id = callback_query.message.chat.id
    
    try:
        # Parse callback data: "seekback chat_id seconds"
        parts = callback_data.split()
        if len(parts) != 3:
            return await callback_query.answer("❌ Invalid callback data!", show_alert=True)
        
        seconds = int(parts[2])
        await handle_seek_inline(callback_query, chat_id, seconds, True, _)
        
    except ValueError:
        await callback_query.answer("❌ Invalid seek value!", show_alert=True)
    except Exception as e:
        await callback_query.answer("❌ Seek operation failed!", show_alert=True)


async def handle_seek_inline(callback_query: CallbackQuery, chat_id: int, seconds: int, is_backward: bool, _):
    """Core function to handle seek operations for inline buttons"""
    try:
        playing = db.get(chat_id)
        if not playing:
            return await callback_query.answer("❌ Nothing is currently playing!", show_alert=True)
        
        duration_seconds = int(playing[0]["seconds"])
        if duration_seconds == 0:
            return await callback_query.answer("❌ Cannot seek in live streams!", show_alert=True)
        
        file_path = playing[0]["file"]
        duration_played = int(playing[0]["played"])
        duration = playing[0]["dur"]
        
        # Calculate seek position
        if is_backward:
            if (duration_played - seconds) <= 10:
                return await callback_query.answer(
                    f"❌ Cannot seek backward! Current: {seconds_to_min(duration_played)}/{duration}",
                    show_alert=True
                )
            to_seek = duration_played - seconds + 1
        else:
            if (duration_seconds - (duration_played + seconds)) <= 10:
                return await callback_query.answer(
                    f"❌ Cannot seek forward! Current: {seconds_to_min(duration_played)}/{duration}",
                    show_alert=True
                )
            to_seek = duration_played + seconds + 1
        
        # Handle different file types
        if "vid_" in file_path:
            n, file_path = await YouTube.video(playing[0]["vidid"], True)
            if n == 0:
                return await callback_query.answer("❌ Failed to get video file!", show_alert=True)
        
        # Check for speed path
        check = playing[0].get("speed_path")
        if check:
            file_path = check
        
        if "index_" in file_path:
            file_path = playing[0]["vidid"]
        
        # Perform the seek operation
        try:
            await Anony.seek_stream(
                chat_id,
                file_path,
                seconds_to_min(to_seek),
                duration,
                playing[0]["streamtype"],
            )
        except Exception as e:
            return await callback_query.answer("❌ Failed to seek! Try again.", show_alert=True)
        
        # Update the database
        if is_backward:
            db[chat_id][0]["played"] -= seconds
        else:
            db[chat_id][0]["played"] += seconds
        
        # Show success message
        direction_icon = "⏪" if is_backward else "⏩"
        success_msg = f"{direction_icon} {seconds}s → {seconds_to_min(to_seek)}"
        await callback_query.answer(success_msg, show_alert=False)
        
    except Exception as e:
        await callback_query.answer("❌ An error occurred during seek operation!", show_alert=True)


# Additional callback handlers for specific seek amounts (if needed)
@app.on_callback_query(filters.regex("ADMIN Seek10") & ~BANNED_USERS)
@ActualAdminCB
async def seek_10_forward(cli, callback_query: CallbackQuery, _):
    chat_id = callback_query.message.chat.id
    await handle_seek_inline(callback_query, chat_id, 10, False, _)


@app.on_callback_query(filters.regex("ADMIN Seek20") & ~BANNED_USERS)
@ActualAdminCB
async def seek_20_forward(cli, callback_query: CallbackQuery, _):
    chat_id = callback_query.message.chat.id
    await handle_seek_inline(callback_query, chat_id, 20, False, _)


@app.on_callback_query(filters.regex("ADMIN SeekBack10") & ~BANNED_USERS)
@ActualAdminCB
async def seek_10_backward(cli, callback_query: CallbackQuery, _):
    chat_id = callback_query.message.chat.id
    await handle_seek_inline(callback_query, chat_id, 10, True, _)


@app.on_callback_query(filters.regex("ADMIN SeekBack20") & ~BANNED_USERS)
@ActualAdminCB
async def seek_20_backward(cli, callback_query: CallbackQuery, _):
    chat_id = callback_query.message.chat.id
    await handle_seek_inline(callback_query, chat_id, 20, True, _)
