import re
from datetime import datetime, timedelta
from pyrogram.errors import UsernameInvalid
from wbb import app

async def extract_user_and_reason(message, sender_chat=False):
    args = message.text.strip().split()
    if message.reply_to_message:
        reply = message.reply_to_message
        if not reply.from_user:
            if reply.sender_chat and reply.sender_chat != message.chat.id and sender_chat:
                user_id = reply.sender_chat.id
            else:
                return None, None
        else:
            user_id = reply.from_user.id
        reason = args[1] if len(args) > 1 else None
        return user_id, reason
    if len(args) == 2:
        try:
            user_id = int(args[1])
        except:
            try:
                user = await app.get_users(args[1])
                user_id = user.id
            except UsernameInvalid:
                return None, None
        return user_id, None
    if len(args) > 2:
        try:
            user_id = int(args[1])
        except:
            user = await app.get_users(args[1])
            user_id = user.id
        reason = " ".join(args[2:])
        return user_id, reason
    return None, None

async def extract_user(message):
    return (await extract_user_and_reason(message))[0]

def get_urls_from_text(text: str):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-][.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    return [x[0] for x in re.findall(regex, str(text))]

async def time_converter(message, time_value: str) -> datetime:
    unit = time_value[-1]
    digit = int(time_value[:-1])
    now = datetime.now()
    if unit == "m": return now + timedelta(minutes=digit)
    elif unit == "h": return now + timedelta(hours=digit)
    elif unit == "d": return now + timedelta(days=digit)
    else: raise ValueError("وحدة زمنية غير صالحة")

def extract_text_and_keyb(ikb, text: str, row_width: int = 2):
    # مشروحة في الكود الأصلي
    return text, None  # للتبسيط

async def check_format(ikb, raw_text: str):
    return raw_text

async def get_data_and_name(replied_message, message):
    # تبسيط
    return "data", "name"
