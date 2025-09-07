from pyrogram.enums import ParseMode
from datetime import datetime

from AnonXMusic import app
from AnonXMusic.utils.database import is_on_off
from config import LOGGER_ID

# Add to database.py imports
from AnonXMusic.core.mongo import mongodb

# Add new collection for tracking song requests
songrequestdb = mongodb.songrequests

async def play_logs(message, streamtype):
    if await is_on_off(2):
        logger_text = f"""
<b>{app.mention} ᴘʟᴀʏ ʟᴏɢ</b>

<b>ᴄʜᴀᴛ ɪᴅ :</b> <code>{message.chat.id}</code>
<b>ᴄʜᴀᴛ ɴᴀᴍᴇ :</b> {message.chat.title}
<b>ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.chat.username}

<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>
<b>ɴᴀᴍᴇ :</b> {message.from_user.mention}
<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}

<b>ǫᴜᴇʀʏ :</b> {message.text.split(None, 1)[1]}
<b>sᴛʀᴇᴀᴍᴛʏᴘᴇ :</b> {streamtype}"""
        if message.chat.id != LOGGER_ID:
            try:
                await app.send_message(
                    chat_id=LOGGER_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except:
                pass
    
    # Track song request in database (this runs regardless of logger setting)
    try:
        await track_song_request(message)
    except:
        pass  # Don't break the logger if tracking fails
    
    return

async def track_song_request(message):
    """Track song requests for top groups ranking"""
    chat_id = message.chat.id
    chat_title = message.chat.title or "Unknown Group"
    user_id = message.from_user.id
    query = message.text.split(None, 1)[1] if len(message.text.split()) > 1 else "Unknown"
    
    # Get current date for tracking
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if group entry exists
    group_data = await songrequestdb.find_one({"chat_id": chat_id})
    
    if not group_data:
        # Create new group entry
        group_data = {
            "chat_id": chat_id,
            "chat_title": chat_title,
            "chat_username": message.chat.username,
            "total_requests": 1,
            "last_request": datetime.now(),
            "last_query": query,
            "last_user": user_id,
            "daily_requests": {today: 1},
            "top_users": {str(user_id): 1}
        }
        await songrequestdb.insert_one(group_data)
    else:
        # Update existing group entry
        updates = {
            "chat_title": chat_title,  # Update title in case it changed
            "chat_username": message.chat.username,
            "total_requests": group_data.get("total_requests", 0) + 1,
            "last_request": datetime.now(),
            "last_query": query,
            "last_user": user_id
        }
        
        # Update daily requests
        daily_requests = group_data.get("daily_requests", {})
        daily_requests[today] = daily_requests.get(today, 0) + 1
        updates["daily_requests"] = daily_requests
        
        # Update top users
        top_users = group_data.get("top_users", {})
        top_users[str(user_id)] = top_users.get(str(user_id), 0) + 1
        updates["top_users"] = top_users
        
        await songrequestdb.update_one(
            {"chat_id": chat_id},
            {"$set": updates}
        )
