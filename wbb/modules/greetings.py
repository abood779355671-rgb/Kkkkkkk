"""
MIT License - مترجم للعربية
وحدة الترحيب والكابتشا
"""
import asyncio
import re
from datetime import datetime, timedelta
from random import shuffle
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import ChatAdminRequired, UserNotParticipant
from pyrogram.types import ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup, Message, Chat, User
from wbb import app, WELCOME_DELAY_KICK_SEC, BOT_USERNAME
from wbb.core.decorators.errors import capture_err
from wbb.core.decorators.permissions import adminsOnly
from wbb.core.keyboard import ikb
from wbb.modules.admin import member_permissions
from wbb.modules.notes import extract_urls
from wbb.utils.dbfunctions import (captcha_off, captcha_on, del_welcome, get_captcha_cache, get_welcome, has_solved_captcha_once, is_captcha_on, save_captcha_solved, set_welcome, update_captcha_cache)
from wbb.utils.filter_groups import welcome_captcha_group
from wbb.utils.functions import check_format, extract_text_and_keyb, generate_captcha

__MODULE__ = "الترحيب والكابتشا"
__HELP__ = """
/captcha [تفعيل|تعطيل] - تفعيل/تعطيل نظام الكابتشا للمستخدمين الجدد.

/set_welcome - رد على رسالة (نص، صورة، متحركة) لتعيينها كرسالة ترحيب.
/del_welcome - حذف رسالة الترحيب.
/get_welcome - عرض رسالة الترحيب الحالية.

**ملاحظات التنسيق:**
- {name} : اسم المستخدم
- {chat} : اسم المجموعة
- يمكنك إضافة أزرار باستخدام: نص ~ [زر, رابط]
"""

answers_dicc = []
loop = asyncio.get_running_loop()
loop.create_task(get_initial_captcha_cache())

async def get_initial_captcha_cache():
    global answers_dicc
    answers_dicc = await get_captcha_cache()
    return answers_dicc

async def handle_new_member(member: User, chat: Chat):
    global answers_dicc
    answers_dicc = await get_captcha_cache()
    try:
        if await is_captcha_on(chat.id):
            if await has_solved_captcha_once(chat.id, member.id):
                return await send_welcome_message(chat, member.id)
            await chat.restrict_member(member.id, permissions=ChatPermissions())
            text = f"🔐 **{member.mention}** هل أنت إنسان؟\nحل الكابتشا خلال {WELCOME_DELAY_KICK_SEC} ثانية وإلا سيتم طردك."
            captcha = generate_captcha()
            captcha_image = captcha[0]
            correct = captcha[1]
            wrong_answers = captcha[2]
            buttons = []
            row1 = [InlineKeyboardButton(correct, callback_data=f"captcha_{correct}_{member.id}")]
            row2 = [InlineKeyboardButton(w, callback_data=f"captcha_{w}_{member.id}") for w in wrong_answers[:2]]
            row3 = [InlineKeyboardButton(w, callback_data=f"captcha_{w}_{member.id}") for w in wrong_answers[2:5]]
            row4 = [InlineKeyboardButton(w, callback_data=f"captcha_{w}_{member.id}") for w in wrong_answers[5:8]]
            shuffle(row1); shuffle(row2); shuffle(row3); shuffle(row4)
            keyboard = InlineKeyboardMarkup([row1, row2, row3, row4])
            verification_data = {"chat_id": chat.id, "user_id": member.id, "answer": correct, "attempts": 0}
            answers_dicc.append(verification_data)
            await update_captcha_cache(answers_dicc)
            msg = await app.send_photo(chat.id, captcha_image, caption=text, reply_markup=keyboard)
            asyncio.create_task(kick_after_delay(WELCOME_DELAY_KICK_SEC, msg, member))
        else:
            await send_welcome_message(chat, member.id)
    except ChatAdminRequired:
        pass

@app.on_chat_member_updated(filters.group, group=welcome_captcha_group)
@capture_err
async def welcome(_, update: ChatMemberUpdated):
    if update.new_chat_member and update.new_chat_member.status not in [ChatMemberStatus.RESTRICTED, ChatMemberStatus.BANNED] and not update.old_chat_member:
        member = update.new_chat_member.user
        await handle_new_member(member, update.chat)

async def send_welcome_message(chat: Chat, user_id: int, delete_after: bool = False):
    welcome_type, raw_text, file_id = await get_welcome(chat.id)
    if not raw_text:
        return
    text = raw_text
    keyb = None
    if re.findall(r"\[.+\,.+\]", raw_text):
        text, keyb = extract_text_and_keyb(ikb, raw_text)
    text = text.replace("{chat}", chat.title).replace("{name}", (await app.get_users(user_id)).mention).replace("{id}", str(user_id))
    if welcome_type == "Text":
        m = await app.send_message(chat.id, text, reply_markup=keyb, disable_web_page_preview=True)
    elif welcome_type == "Photo":
        m = await app.send_photo(chat.id, file_id, caption=text, reply_markup=keyb)
    else:  # Animation
        m = await app.send_animation(chat.id, file_id, caption=text, reply_markup=keyb)
    if delete_after:
        await asyncio.sleep(300)
        await m.delete()

async def kick_after_delay(delay, message: Message, user: User):
    await asyncio.sleep(delay)
    global answers_dicc
    for i in answers_dicc[:]:
        if i["user_id"] == user.id and i["chat_id"] == message.chat.id:
            answers_dicc.remove(i)
            await update_captcha_cache(answers_dicc)
    try:
        member = await message.chat.get_member(user.id)
        if member.status == ChatMemberStatus.RESTRICTED:
            await message.chat.ban_member(user.id, until_date=datetime.now()+timedelta(seconds=delay))
            await asyncio.sleep(1)
            await message.chat.unban_member(user.id)
    except UserNotParticipant:
        pass
    await message.delete()

@app.on_callback_query(filters.regex(r"captcha_(.*)"))
async def captcha_callback(_, cq):
    data = cq.data.split("_")
    answer = data[1]
    user_id = int(data[2])
    if cq.from_user.id != user_id:
        return await cq.answer("هذا الزر ليس لك!", show_alert=True)
    correct = None
    for i in answers_dicc:
        if i["user_id"] == user_id and i["chat_id"] == cq.message.chat.id:
            correct = i["answer"]
            break
    if not correct:
        return await cq.answer("انتهت صلاحية الكابتشا، أعد الانضمام.", show_alert=True)
    if answer != correct:
        for i in answers_dicc:
            if i["user_id"] == user_id:
                i["attempts"] += 1
                if i["attempts"] >= 4:
                    answers_dicc.remove(i)
                    await update_captcha_cache(answers_dicc)
                    await cq.message.chat.ban_member(user_id)
                    await asyncio.sleep(1)
                    await cq.message.chat.unban_member(user_id)
                    await cq.message.delete()
                    return await cq.answer("تم طردك لكثرة المحاولات الخاطئة.", show_alert=True)
                await update_captcha_cache(answers_dicc)
                return await cq.answer("إجابة خاطئة، حاول مجدداً.", show_alert=True)
    await cq.answer("✅ تم التحقق بنجاح!", show_alert=True)
    await cq.message.chat.unban_member(user_id)
    await cq.message.delete()
    for i in answers_dicc[:]:
        if i["user_id"] == user_id:
            answers_dicc.remove(i)
            await update_captcha_cache(answers_dicc)
    await save_captcha_solved(cq.message.chat.id, user_id)
    await send_welcome_message(cq.message.chat, user_id, delete_after=True)

@app.on_message(filters.command("captcha") & ~filters.private)
@adminsOnly("can_restrict_members")
async def captcha_toggle(_, message):
    if len(message.command) != 2:
        return await message.reply_text("**الاستخدام:** /captcha [تفعيل|تعطيل]")
    state = message.command[1].lower()
    if state == "تفعيل":
        await captcha_on(message.chat.id)
        await message.reply_text("✅ تم تفعيل الكابتشا للمستخدمين الجدد.")
    elif state == "تعطيل":
        await captcha_off(message.chat.id)
        await message.reply_text("❌ تم تعطيل الكابتشا.")
    else:
        await message.reply_text("خيار غير صالح، استخدم `تفعيل` أو `تعطيل`.")

@app.on_message(filters.command("set_welcome") & ~filters.private)
@adminsOnly("can_change_info")
async def set_welcome_cmd(_, message):
    replied = message.reply_to_message
    if not replied:
        return await message.reply_text("رد على رسالة نصية، صورة، أو متحركة لتعيينها كترحيب.")
    welcome_type = None
    file_id = None
    if replied.text:
        welcome_type = "Text"
        raw_text = replied.text.html
    elif replied.photo:
        welcome_type = "Photo"
        file_id = replied.photo.file_id
        raw_text = replied.caption.html if replied.caption else ""
    elif replied.animation:
        welcome_type = "Animation"
        file_id = replied.animation.file_id
        raw_text = replied.caption.html if replied.caption else ""
    else:
        return await message.reply_text("نوع الوسائط غير مدعوم (نص، صورة، متحركة فقط).")
    if replied.reply_markup and not re.findall(r"\[.+\,.+\]", raw_text):
        urls = extract_urls(replied.reply_markup)
        if urls:
            raw_text += "\n" + "\n".join([f"{name}=[{text}, {url}]" for name, text, url in urls])
    raw_text = await check_format(ikb, raw_text)
    if raw_text is False:
        return await message.reply_text("تنسيق خاطئ، تأكد من كتابة الأزرار بشكل صحيح.")
    await set_welcome(message.chat.id, welcome_type, raw_text, file_id)
    await message.reply_text("✅ تم تعيين رسالة الترحيب بنجاح.")

@app.on_message(filters.command("get_welcome") & ~filters.private)
@adminsOnly("can_change_info")
async def get_welcome_cmd(_, message):
    w_type, text, file_id = await get_welcome(message.chat.id)
    if not text:
        return await message.reply_text("لا توجد رسالة ترحيب مضبوطة.")
    await message.reply_text(f"**نوع الترحيب:** `{w_type}`\n**النص:**\n{text[:500]}")
    if file_id:
        await message.reply_text(f"**File ID:** `{file_id}`")

@app.on_message(filters.command("del_welcome") & ~filters.private)
@adminsOnly("can_change_info")
async def del_welcome_cmd(_, message):
    await del_welcome(message.chat.id)
    await message.reply_text("🗑️ تم حذف رسالة الترحيب.")
