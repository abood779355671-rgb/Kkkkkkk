"""
MIT License - مترجم للعربية
وحدة قفل أنواع معينة من المحتوى
"""
from pyrogram import filters
from pyrogram.errors.exceptions.bad_request_400 import ChatNotModified
from pyrogram.types import ChatPermissions
from wbb import SUDOERS, app
from wbb.core.decorators.errors import capture_err
from wbb.core.decorators.permissions import adminsOnly
from wbb.modules.admin import list_admins
from wbb.utils.functions import get_urls_from_text

__MODULE__ = "الأقفال"
__HELP__ = """
**أوامر القفل والفتح:**
/lock [نوع] - قفل نوع معين من المحتوى.
/unlock [نوع] - فتح قفل نوع معين.

**الأنواع المدعومة:**
- `messages` - الرسائل النصية
- `stickers` - الملصقات
- `gifs` - الرسوم المتحركة
- `media` - الوسائط (صور، فيديو، صوت)
- `games` - الألعاب
- `inline` - الأزرار المضمنة
- `url` - الروابط
- `polls` - الاستطلاعات
- `group_info` - تغيير معلومات المجموعة
- `useradd` - إضافة أعضاء جدد
- `pin` - تثبيت الرسائل

مثال: `/lock url` لقفل الروابط.
"""

data = {
    "messages": "can_send_messages",
    "stickers": "can_send_other_messages",
    "gifs": "can_send_other_messages",
    "media": "can_send_media_messages",
    "games": "can_send_other_messages",
    "inline": "can_send_other_messages",
    "url": "can_add_web_page_previews",
    "polls": "can_send_polls",
    "group_info": "can_change_info",
    "useradd": "can_invite_users",
    "pin": "can_pin_messages",
}

async def current_chat_permissions(chat_id):
    perm = (await app.get_chat(chat_id)).permissions
    perms = []
    if perm.can_send_messages: perms.append("can_send_messages")
    if perm.can_send_media_messages: perms.append("can_send_media_messages")
    if perm.can_send_other_messages: perms.append("can_send_other_messages")
    if perm.can_add_web_page_previews: perms.append("can_add_web_page_previews")
    if perm.can_send_polls: perms.append("can_send_polls")
    if perm.can_change_info: perms.append("can_change_info")
    if perm.can_invite_users: perms.append("can_invite_users")
    if perm.can_pin_messages: perms.append("can_pin_messages")
    return perms

async def toggle_lock(message, lock_type, lock: bool):
    perms = await current_chat_permissions(message.chat.id)
    if lock:
        if lock_type not in perms:
            return await message.reply_text("🔒 هذا النوع مقفل بالفعل.")
        perms.remove(lock_type)
    else:
        if lock_type in perms:
            return await message.reply_text("🔓 هذا النوع مفتوح بالفعل.")
        perms.append(lock_type)
    try:
        await app.set_chat_permissions(message.chat.id, ChatPermissions(**{p: True for p in perms}))
    except ChatNotModified:
        return await message.reply_text("لإلغاء قفل هذا النوع، يجب أولاً فتح `messages`.")
    await message.reply_text("🔒 **مقفل**" if lock else "🔓 **مفتوح**")

@app.on_message(filters.command(["lock", "unlock"]) & ~filters.private)
@adminsOnly("can_restrict_members")
async def locks_func(_, message):
    if len(message.command) != 2:
        return await message.reply_text("**الاستخدام:** /lock [نوع]  أو /unlock [نوع]")
    param = message.command[1].lower()
    if param not in data and param != "all":
        return await message.reply_text("نوع غير صالح. راجع المساعدة.")
    if param == "all" and message.command[0] == "lock":
        await app.set_chat_permissions(message.chat.id, ChatPermissions())
        await message.reply_text("🔒 تم قفل كل شيء.")
    elif param == "all" and message.command[0] == "unlock":
        await app.set_chat_permissions(message.chat.id, ChatPermissions(
            can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True,
            can_add_web_page_previews=True, can_send_polls=True, can_change_info=False,
            can_invite_users=True, can_pin_messages=False
        ))
        await message.reply_text("🔓 تم فتح كل شيء.")
    else:
        await toggle_lock(message, data[param], message.command[0] == "lock")

@app.on_message(filters.command("locks") & ~filters.private)
@capture_err
async def locktypes(_, message):
    perms = await current_chat_permissions(message.chat.id)
    if not perms:
        return await message.reply_text("لا توجد صلاحيات مقفلة.")
    text = "**الصلاحيات الحالية:**\n" + "\n".join(f"- `{p}`" for p in perms)
    await message.reply_text(text)

@app.on_message(filters.text & ~filters.private, group=69)
async def url_detector(_, message):
    user = message.from_user
    if not user or user.id in SUDOERS:
        return
    admins = await list_admins(message.chat.id)
    if user.id in admins:
        return
    perms = await current_chat_permissions(message.chat.id)
    if "can_add_web_page_previews" not in perms:
        urls = get_urls_from_text(message.text)
        if urls:
            try:
                await message.delete()
            except:
                await message.reply_text("🚫 الروابط ممنوعة في هذه المجموعة.")
