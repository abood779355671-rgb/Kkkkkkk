"""
MIT License - مترجم للعربية
وحدة الملاحظات - حفظ واستدعاء الملاحظات باستخدام # noting
"""

import re
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from wbb import app, SUDOERS, USERBOT_PREFIX, app2, eor
from wbb.core.decorators.errors import capture_err
from wbb.core.decorators.permissions import adminsOnly
from wbb.core.keyboard import ikb
from wbb.modules.admin import member_permissions
from wbb.utils.dbfunctions import delete_note, deleteall_notes, get_note, get_note_names, save_note
from wbb.utils.functions import check_format, extract_text_and_keyb, get_data_and_name

__MODULE__ = "الملاحظات"
__HELP__ = """
**أوامر الملاحظات:**

/notes - عرض جميع الملاحظات في الدردشة.

/save [اسم_الملاحظة] - حفظ ملاحظة (بالرد على رسالة).

#اسم_الملاحظة - استدعاء الملاحظة.

/delete [اسم_الملاحظة] - حذف ملاحظة.
/deleteall - حذف جميع الملاحظات (نهائياً).

**ملاحظة:** يمكنك استخدام التنسيق (Markdown) والأزرار في الملاحظات.
"""

def extract_urls(reply_markup):
    urls = []
    if reply_markup.inline_keyboard:
        buttons = reply_markup.inline_keyboard
        for i, row in enumerate(buttons):
            for j, button in enumerate(row):
                if button.url:
                    name = "\n~\nbutton" if i * len(row) + j + 1 == 1 else f"button{i * len(row) + j + 1}"
                    urls.append((name, button.text, button.url))
    return urls

@app2.on_message(filters.command("save", prefixes=USERBOT_PREFIX) & SUDOERS & ~filters.via_bot)
@app.on_message(filters.command("save") & ~filters.private)
@adminsOnly("can_change_info")
async def save_note_cmd(_, message):
    try:
        if len(message.command) < 2:
            await eor(message, text="**الاستخدام:**\nرد على رسالة بـ /save [اسم_الملاحظة]")
            return
        replied = message.reply_to_message or message
        data, name = await get_data_and_name(replied, message)
        if data == "error":
            return await eor(message, text="الاستخدام غير صحيح.")
        _type = None
        file_id = None
        if replied.text: _type = "text"
        elif replied.sticker: _type, file_id = "sticker", replied.sticker.file_id
        elif replied.animation: _type, file_id = "animation", replied.animation.file_id
        elif replied.photo: _type, file_id = "photo", replied.photo.file_id
        elif replied.document: _type, file_id = "document", replied.document.file_id
        elif replied.video: _type, file_id = "video", replied.video.file_id
        elif replied.video_note: _type, file_id = "video_note", replied.video_note.file_id
        elif replied.audio: _type, file_id = "audio", replied.audio.file_id
        elif replied.voice: _type, file_id = "voice", replied.voice.file_id
        if not _type:
            return await eor(message, text="نوع الوسائط غير مدعوم.")
        if replied.reply_markup and not re.findall(r"\[.+\,.+\]", data):
            urls = extract_urls(replied.reply_markup)
            if urls:
                response = "\n".join([f"{name}=[{text}, {url}]" for name, text, url in urls])
                data = data + response
        if data:
            data = await check_format(ikb, data)
            if not data:
                return await eor(message, text="تنسيق خاطئ، راجع المساعدة.")
        note = {"type": _type, "data": data, "file_id": file_id}
        chat_id = USERBOT_ID if message.text.startswith(USERBOT_PREFIX) else message.chat.id
        await save_note(chat_id, name, note)
        await eor(message, text=f"**تم حفظ الملاحظة `{name}`**")
    except UnboundLocalError:
        await eor(message, text="الرسالة التي رد عليها غير متاحة، أعد توجيهها وحاول مجدداً.")

@app2.on_message(filters.command("notes", prefixes=USERBOT_PREFIX) & ~filters.forwarded & ~filters.via_bot & SUDOERS)
@app.on_message(filters.command("notes") & ~filters.private)
@capture_err
async def get_notes_cmd(_, message):
    prefix = message.text.split()[0][0]
    is_ubot = prefix == USERBOT_PREFIX
    chat_id = USERBOT_ID if is_ubot else message.chat.id
    notes = await get_note_names(chat_id)
    if not notes:
        return await eor(message, text="لا توجد ملاحظات في هذه الدردشة.")
    notes.sort()
    msg = f"**قائمة الملاحظات في {'الحساب المساعد' if is_ubot else message.chat.title}:**\n" + "\n".join(f"- `{n}`" for n in notes)
    await eor(message, text=msg)

@app2.on_message(filters.command("get", prefixes=USERBOT_PREFIX) & ~filters.forwarded & ~filters.via_bot & SUDOERS)
async def get_one_note_userbot(_, message):
    if len(message.command) < 2:
        return await eor(message, text="أرسل اسم الملاحظة.")
    name = message.command[1]
    note = await get_note(USERBOT_ID, name)
    if not note:
        return await eor(message, text="الملاحظة غير موجودة.")
    await send_note_reply(message, note)

@app.on_message(filters.regex(r"^#.+") & filters.text & ~filters.private)
@capture_err
async def get_one_note(_, message):
    from_user = message.from_user or message.sender_chat
    name = message.text.replace("#", "", 1).strip()
    if not name:
        return
    note = await get_note(message.chat.id, name)
    if not note:
        return
    data = note["data"]
    if data:
        data = data.replace("{chat}", message.chat.title)
        if from_user:
            mention = from_user.mention if hasattr(from_user, 'mention') else from_user.title
            data = data.replace("{name}", mention)
        if re.findall(r"\[.+\,.+\]", data):
            kb = extract_text_and_keyb(ikb, data)
            if kb:
                data, keyb = kb
    await send_note_reply(message, note, data)

async def send_note_reply(message, note, custom_data=None):
    _type = note["type"]
    data = custom_data if custom_data is not None else note["data"]
    file_id = note.get("file_id")
    keyb = None
    if data and re.findall(r"\[.+\,.+\]", data):
        kb = extract_text_and_keyb(ikb, data)
        if kb:
            data, keyb = kb
    if _type == "text":
        await message.reply_text(data, reply_markup=keyb, disable_web_page_preview=True)
    elif _type == "sticker":
        await message.reply_sticker(file_id)
    elif _type == "animation":
        await message.reply_animation(file_id, caption=data, reply_markup=keyb)
    elif _type == "photo":
        await message.reply_photo(file_id, caption=data, reply_markup=keyb)
    elif _type == "document":
        await message.reply_document(file_id, caption=data, reply_markup=keyb)
    elif _type == "video":
        await message.reply_video(file_id, caption=data, reply_markup=keyb)
    elif _type == "video_note":
        await message.reply_video_note(file_id)
    elif _type == "audio":
        await message.reply_audio(file_id, caption=data, reply_markup=keyb)
    elif _type == "voice":
        await message.reply_voice(file_id, caption=data, reply_markup=keyb)

@app2.on_message(filters.command("delete", prefixes=USERBOT_PREFIX) & ~filters.forwarded & ~filters.via_bot & SUDOERS)
@app.on_message(filters.command("delete") & ~filters.private)
@adminsOnly("can_change_info")
async def del_note_cmd(_, message):
    if len(message.command) < 2:
        return await eor(message, text="**الاستخدام:** /delete [اسم_الملاحظة]")
    name = message.command[1]
    prefix = message.text[0]
    is_ubot = prefix == USERBOT_PREFIX
    chat_id = USERBOT_ID if is_ubot else message.chat.id
    deleted = await delete_note(chat_id, name)
    await eor(message, text=f"تم حذف الملاحظة `{name}`" if deleted else "الملاحظة غير موجودة.")

@app.on_message(filters.command("deleteall") & ~filters.private)
@adminsOnly("can_change_info")
async def delete_all_notes(_, message):
    if not await get_note_names(message.chat.id):
        return await message.reply_text("لا توجد ملاحظات للحذف.")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("نعم", callback_data="delete_yes"), InlineKeyboardButton("لا", callback_data="delete_no")]
    ])
    await message.reply_text("هل أنت متأكد من حذف جميع الملاحظات نهائياً؟", reply_markup=keyboard)

@app.on_callback_query(filters.regex("delete_(.*)"))
async def delete_all_cb(_, cb: CallbackQuery):
    chat_id = cb.message.chat.id
    from_user = cb.from_user
    permissions = await member_permissions(chat_id, from_user.id)
    if "can_change_info" not in permissions and from_user.id not in SUDOERS:
        return await cb.answer("ليس لديك صلاحية حذف الملاحظات.", show_alert=True)
    if cb.data == "delete_yes":
        await deleteall_notes(chat_id)
        await cb.message.edit("**تم حذف جميع الملاحظات بنجاح.**")
    else:
        await cb.message.delete()
