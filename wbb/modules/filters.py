import re
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from wbb import app
from wbb.core.decorators.errors import capture_err
from wbb.core.decorators.permissions import adminsOnly
from wbb.core.keyboard import ikb
from wbb.modules.admin import member_permissions
from wbb.utils.dbfunctions import delete_filter, deleteall_filters, get_filter, get_filters_names, save_filter
from wbb.utils.filter_groups import chat_filters_group
from wbb.utils.functions import check_format, extract_text_and_keyb, get_data_and_name

__MODULE__ = "الفلاتر"
__HELP__ = """
/filters - عرض كل الفلاتر في الدردشة.
/filter [اسم_الفلاتر] - حفظ فلتر (بالرد على رسالة).

أنواع الفلاتر المدعومة: نص، متحركة، صورة، مستند، فيديو، صوت، ملصق.

للكلمات المركبة استخدم شرطة سفلية: /filter مرحبا_بالجميع

/stop [اسم_الفلاتر] - حذف فلتر.
/stopall - حذف جميع الفلاتر في الدردشة.
"""

@app.on_message(filters.command("filter") & ~filters.private)
@adminsOnly("can_change_info")
async def save_filters(_, message):
    try:
        if len(message.command) < 2:
            return await message.reply_text("الاستخدام:\nرد على رسالة بـ /filter [اسم_الفلتر]")
        replied = message.reply_to_message or message
        data, name = await get_data_and_name(replied, message)
        if data == "error":
            return await message.reply_text("الاستخدام غير صحيح.")
        _type = None
        file_id = None
        if replied.text: _type = "text"
        elif replied.sticker: _type, file_id = "sticker", replied.sticker.file_id
        elif replied.animation: _type, file_id = "animation", replied.animation.file_id
        elif replied.photo: _type, file_id = "photo", replied.photo.file_id
        elif replied.document: _type, file_id = "document", replied.document.file_id
        elif replied.video: _type, file_id = "video", replied.video.file_id
        elif replied.audio: _type, file_id = "audio", replied.audio.file_id
        elif replied.voice: _type, file_id = "voice", replied.voice.file_id
        if not _type:
            return await message.reply_text("نوع الوسائط غير مدعوم.")
        if data:
            data = await check_format(ikb, data)
            if not data: return await message.reply_text("تنسيق خاطئ، راجع المساعدة.")
        _filter = {"type": _type, "data": data, "file_id": file_id}
        await save_filter(message.chat.id, name, _filter)
        await message.reply_text(f"تم حفظ الفلتر `{name}`")
    except Exception as e:
        await message.reply_text(f"خطأ: {e}")

@app.on_message(filters.command("filters") & ~filters.private)
@capture_err
async def get_filterss(_, message):
    _filters = await get_filters_names(message.chat.id)
    if not _filters:
        return await message.reply_text("لا توجد فلاتر في هذه الدردشة.")
    _filters.sort()
    msg = f"قائمة الفلاتر في {message.chat.title}:\n" + "\n".join(f"- `{f}`" for f in _filters)
    await message.reply_text(msg)

@app.on_message(filters.command("stop") & ~filters.private)
@adminsOnly("can_change_info")
async def del_filter(_, message):
    if len(message.command) < 2:
        return await message.reply_text("الاستخدام: /stop [اسم_الفلتر]")
    name = message.text.split(None, 1)[1].strip()
    deleted = await delete_filter(message.chat.id, name)
    await message.reply_text(f"تم حذف الفلتر `{name}`" if deleted else "الفلتر غير موجود.")

@app.on_message(filters.text & ~filters.private & ~filters.channel & ~filters.via_bot & ~filters.forwarded, group=chat_filters_group)
@capture_err
async def filters_re(_, message):
    text = message.text.lower().strip()
    if not text: return
    chat_id = message.chat.id
    names = await get_filters_names(chat_id)
    for word in names:
        if re.search(r"( |^|[^\w])" + re.escape(word) + r"( |$|[^\w])", text, re.IGNORECASE):
            _filter = await get_filter(chat_id, word)
            data = _filter["data"]
            file_id = _filter.get("file_id")
            keyb = None
            if data:
                data = data.replace("{chat}", message.chat.title)
                if message.from_user: data = data.replace("{name}", message.from_user.mention)
                if re.findall(r"\[.+\,.+\]", data):
                    kb = extract_text_and_keyb(ikb, data)
                    if kb: data, keyb = kb
            # إرسال حسب النوع
            if _filter["type"] == "text":
                await message.reply_text(data, reply_markup=keyb, disable_web_page_preview=True)
            elif _filter["type"] == "sticker":
                await message.reply_sticker(file_id)
            elif _filter["type"] == "animation":
                await message.reply_animation(file_id, caption=data, reply_markup=keyb)
            elif _filter["type"] == "photo":
                await message.reply_photo(file_id, caption=data, reply_markup=keyb)
            elif _filter["type"] == "document":
                await message.reply_document(file_id, caption=data, reply_markup=keyb)
            elif _filter["type"] == "video":
                await message.reply_video(file_id, caption=data, reply_markup=keyb)
            elif _filter["type"] == "audio":
                await message.reply_audio(file_id, caption=data, reply_markup=keyb)
            elif _filter["type"] == "voice":
                await message.reply_voice(file_id, caption=data, reply_markup=keyb)
            return

@app.on_message(filters.command("stopall") & ~filters.private)
@adminsOnly("can_change_info")
async def stop_all(_, message):
    if not await get_filters_names(message.chat.id):
        return await message.reply_text("لا توجد فلاتر للحذف.")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("نعم", callback_data="stop_yes"), InlineKeyboardButton("لا", callback_data="stop_no")]])
    await message.reply_text("هل أنت متأكد من حذف جميع الفلاتر؟", reply_markup=keyboard)

@app.on_callback_query(filters.regex("stop_(.*)"))
async def stop_all_cb(_, cb):
    chat_id = cb.message.chat.id
    if cb.data.split("_",1)[1] == "yes":
        await deleteall_filters(chat_id)
        await cb.message.edit("تم حذف جميع الفلاتر.")
    else:
        await cb.message.delete()
