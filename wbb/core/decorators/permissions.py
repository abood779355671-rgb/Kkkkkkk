from functools import wraps
from traceback import format_exc as err
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.types import Message
from wbb import SUDOERS, app
from wbb.modules.admin import member_permissions

async def authorised(func, subFunc2, client, message, *args, **kwargs):
    chatID = message.chat.id
    try:
        await func(client, message, *args, **kwargs)
    except ChatWriteForbidden:
        await app.leave_chat(chatID)
    except Exception as e:
        try:
            await message.reply_text(str(e.MESSAGE))
        except AttributeError:
            await message.reply_text(str(e))
    return subFunc2

async def unauthorised(message: Message, permission, subFunc2):
    text = f"ليس لديك صلاحية `{permission}` لتنفيذ هذا الأمر."
    try:
        await message.reply_text(text)
    except ChatWriteForbidden:
        await app.leave_chat(message.chat.id)
    return subFunc2

def adminsOnly(permission):
    def subFunc(func):
        @wraps(func)
        async def subFunc2(client, message: Message, *args, **kwargs):
            if not message.from_user:
                if message.sender_chat and message.sender_chat.id == message.chat.id:
                    return await authorised(func, subFunc2, client, message, *args, **kwargs)
                return await unauthorised(message, permission, subFunc2)
            userID = message.from_user.id
            permissions = await member_permissions(message.chat.id, userID)
            if userID not in SUDOERS and permission not in permissions:
                return await unauthorised(message, permission, subFunc2)
            return await authorised(func, subFunc2, client, message, *args, **kwargs)
        return subFunc2
    return subFunc
