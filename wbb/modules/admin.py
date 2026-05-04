"""
وحدة الإدارة - مترجمة للعربية
"""
import asyncio
import re
from datetime import datetime, timedelta
from time import time

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType
from pyrogram.errors import FloodWait
from pyrogram.types import CallbackQuery, ChatMemberUpdated, ChatPermissions, ChatPrivileges, Message

from wbb import BOT_ID, SUDOERS, app, log
from wbb.core.decorators.errors import capture_err
from wbb.core.decorators.permissions import adminsOnly
from wbb.core.keyboard import ikb
from wbb.utils.dbfunctions import add_warn, get_warn, int_to_alpha, remove_warns, save_filter
from wbb.utils.functions import extract_user, extract_user_and_reason, time_converter

__MODULE__ = "الإدارة"
__HELP__ = """
**أوامر الإدارة:**

/ban - حظر عضو
/dban - حظر العضو وحذف رسالته
/tban - حظر مؤقت (مثال: /tban 2h)
/unban - إلغاء الحظر
/warn - تحذير عضو
/dwarn - تحذير وحذف الرسالة
/rmwarns - إزالة التحذيرات
/warns - عرض تحذيرات العضو
/kick - طرد العضو
/dkick - طرد وحذف الرسالة
/purge - مسح الرسائل (بالرد)
/del - حذف الرسالة المردود عليها
/promote - ترقية عضو
/fullpromote - ترقية بكل الصلاحيات
/demote - تنزيل مشرف
/pin - تثبيت رسالة
/unpin - إلغاء التثبيت
/mute - كتم عضو
/tmute - كتم مؤقت (مثال: /tmute 1h)
/unmute - إلغاء الكتم
/ban_ghosts - حظر الحسابات المحذوفة
/report - الإبلاغ عن عضو للمشرفين
/invite - الحصول على رابط دعوة المجموعة
"""

async def member_permissions(chat_id: int, user_id: int):
    perms = []
    member = (await app.get_chat_member(chat_id, user_id)).privileges
    if not member:
        return []
    if member.can_post_messages: perms.append("can_post_messages")
    if member.can_edit_messages: perms.append("can_edit_messages")
    if member.can_delete_messages: perms.append("can_delete_messages")
    if member.can_restrict_members: perms.append("can_restrict_members")
    if member.can_promote_members: perms.append("can_promote_members")
    if member.can_change_info: perms.append("can_change_info")
    if member.can_invite_users: perms.append("can_invite_users")
    if member.can_pin_messages: perms.append("can_pin_messages")
    if member.can_manage_video_chats: perms.append("can_manage_video_chats")
    return perms

# كاش المشرفين
admins_in_chat = {}
async def list_admins(chat_id: int):
    global admins_in_chat
    if chat_id in admins_in_chat and time() - admins_in_chat[chat_id]["last_updated_at"] < 3600:
        return admins_in_chat[chat_id]["data"]
    admins_in_chat[chat_id] = {
        "last_updated_at": time(),
        "data": [member.user.id async for member in app.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS)]
    }
    return admins_in_chat[chat_id]["data"]

@app.on_chat_member_updated()
async def admin_cache_func(_, cmu: ChatMemberUpdated):
    if cmu.old_chat_member and cmu.old_chat_member.promoted_by:
        admins_in_chat[cmu.chat.id] = {
            "last_updated_at": time(),
            "data": [member.user.id async for member in app.get_chat_members(cmu.chat.id, filter=ChatMembersFilter.ADMINISTRATORS)]
        }

# مسح الرسائل
@app.on_message(filters.command("purge") & ~filters.private)
@adminsOnly("can_delete_messages")
async def purgeFunc(_, message: Message):
    repliedmsg = message.reply_to_message
    await message.delete()
    if not repliedmsg:
        return await message.reply_text("الرد على رسالة لبدء المسح منها.")
    cmd = message.command
    if len(cmd) > 1 and cmd[1].isdigit():
        purge_to = repliedmsg.id + int(cmd[1])
        if purge_to > message.id: purge_to = message.id
    else:
        purge_to = message.id
    chat_id = message.chat.id
    message_ids = []
    for mid in range(repliedmsg.id, purge_to):
        message_ids.append(mid)
        if len(message_ids) == 100:
            await app.delete_messages(chat_id, message_ids, revoke=True)
            message_ids = []
    if message_ids:
        await app.delete_messages(chat_id, message_ids, revoke=True)

# طرد
@app.on_message(filters.command(["kick", "dkick"]) & ~filters.private)
@adminsOnly("can_restrict_members")
async def kickFunc(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    if not user_id: return await message.reply_text("لم أجد هذا المستخدم.")
    if user_id == BOT_ID: return await message.reply_text("لا يمكنني طرد نفسي.")
    if user_id in SUDOERS: return await message.reply_text("لا يمكنك طرد مطور البوت.")
    if user_id in (await list_admins(message.chat.id)): return await message.reply_text("لا يمكن طرد مشرف.")
    mention = (await app.get_users(user_id)).mention
    msg = f"**تم طرد:** {mention}\n**بواسطة:** {message.from_user.mention if message.from_user else 'مجهول'}\n**السبب:** {reason or 'بدون سبب.'}"
    if message.command[0][0] == "d":
        await message.reply_to_message.delete()
    await message.chat.ban_member(user_id)
    await message.reply_text(msg)
    await asyncio.sleep(1)
    await message.chat.unban_member(user_id)

# حظر
@app.on_message(filters.command(["ban", "dban", "tban"]) & ~filters.private)
@adminsOnly("can_restrict_members")
async def banFunc(_, message: Message):
    user_id, reason = await extract_user_and_reason(message, sender_chat=True)
    if not user_id: return await message.reply_text("لم أجد هذا المستخدم.")
    if user_id == BOT_ID: return await message.reply_text("لا يمكنني حظر نفسي.")
    if user_id in SUDOERS: return await message.reply_text("لا يمكن حظر مطور البوت.")
    if user_id in (await list_admins(message.chat.id)): return await message.reply_text("لا يمكن حظر مشرف.")
    mention = (await app.get_users(user_id)).mention
    msg = f"**تم حظر:** {mention}\n**بواسطة:** {message.from_user.mention if message.from_user else 'مجهول'}\n"
    if message.command[0][0] == "d":
        await message.reply_to_message.delete()
    if message.command[0] == "tban":
        split = reason.split(None, 1)
        time_value = split[0]
        temp_reason = split[1] if len(split) > 1 else ""
        until = await time_converter(message, time_value)
        msg += f"**مدة الحظر:** {time_value}\n**السبب:** {temp_reason}"
        await message.chat.ban_member(user_id, until_date=until)
    else:
        if reason: msg += f"**السبب:** {reason}"
        await message.chat.ban_member(user_id)
    await message.reply_text(msg)

# إلغاء حظر
@app.on_message(filters.command("unban") & ~filters.private)
@adminsOnly("can_restrict_members")
async def unban_func(_, message: Message):
    reply = message.reply_to_message
    if reply and reply.sender_chat and reply.sender_chat != message.chat.id:
        return await message.reply_text("لا يمكنك إلغاء حظر قناة.")
    if len(message.command) == 2:
        user = message.text.split(None, 1)[1]
    elif len(message.command) == 1 and reply:
        user = reply.from_user.id
    else:
        return await message.reply_text("أرسل معرف المستخدم أو رد على رسالته.")
    await message.chat.unban_member(user)
    umention = (await app.get_users(user)).mention
    await message.reply_text(f"تم إلغاء حظر {umention}")

# ترقية
@app.on_message(filters.command(["promote", "fullpromote"]) & ~filters.private)
@adminsOnly("can_promote_members")
async def promoteFunc(_, message: Message):
    user_id = await extract_user(message)
    if not user_id: return await message.reply_text("لم أجد هذا المستخدم.")
    bot = (await app.get_chat_member(message.chat.id, BOT_ID)).privileges
    if user_id == BOT_ID: return await message.reply_text("لا يمكنني ترقية نفسي.")
    if not bot or not bot.can_promote_members: return await message.reply_text("ليس لدي صلاحية الترقية.")
    umention = (await app.get_users(user_id)).mention
    if message.command[0][0] == "f":  # fullpromote
        await message.chat.promote_member(user_id, privileges=ChatPrivileges(
            can_change_info=bot.can_change_info,
            can_invite_users=bot.can_invite_users,
            can_delete_messages=bot.can_delete_messages,
            can_restrict_members=bot.can_restrict_members,
            can_pin_messages=bot.can_pin_messages,
            can_promote_members=bot.can_promote_members,
            can_manage_chat=bot.can_manage_chat,
            can_manage_video_chats=bot.can_manage_video_chats
        ))
        await message.reply_text(f"تمت الترقية الكاملة لـ {umention}")
    else:
        await message.chat.promote_member(user_id, privileges=ChatPrivileges(
            can_change_info=False,
            can_invite_users=bot.can_invite_users,
            can_delete_messages=bot.can_delete_messages,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_chat=bot.can_manage_chat,
            can_manage_video_chats=bot.can_manage_video_chats
        ))
        await message.reply_text(f"تمت ترقية {umention}")

# تنزيل
@app.on_message(filters.command("demote") & ~filters.private)
@adminsOnly("can_promote_members")
async def demote(_, message: Message):
    user_id = await extract_user(message)
    if not user_id: return await message.reply_text("لم أجد هذا المستخدم.")
    if user_id == BOT_ID: return await message.reply_text("لا يمكنني تنزيل نفسي.")
    if user_id in SUDOERS: return await message.reply_text("لا يمكن تنزيل مطور البوت.")
    member = await app.get_chat_member(message.chat.id, user_id)
    if member.status == ChatMemberStatus.ADMINISTRATOR:
        await message.chat.promote_member(user_id, privileges=ChatPrivileges(
            can_change_info=False, can_invite_users=False, can_delete_messages=False,
            can_restrict_members=False, can_pin_messages=False, can_promote_members=False,
            can_manage_chat=False, can_manage_video_chats=False
        ))
        await message.reply_text(f"تم تنزيل {(await app.get_users(user_id)).mention}")
    else:
        await message.reply_text("هذا العضو ليس مشرفاً.")

# تثبيت
@app.on_message(filters.command(["pin", "unpin"]) & ~filters.private)
@adminsOnly("can_pin_messages")
async def pin(_, message: Message):
    if not message.reply_to_message: return await message.reply_text("الرد على رسالة لتثبيتها/إلغاء تثبيتها.")
    r = message.reply_to_message
    if message.command[0][0] == "u":
        await r.unpin()
        await message.reply_text(f"**تم إلغاء تثبيت [هذه]({r.link}) الرسالة.**", disable_web_page_preview=True)
    else:
        await r.pin(disable_notification=True)
        await message.reply(f"**تم تثبيت [هذه]({r.link}) الرسالة.**", disable_web_page_preview=True)

# كتم
@app.on_message(filters.command(["mute", "tmute"]) & ~filters.private)
@adminsOnly("can_restrict_members")
async def mute(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    if not user_id: return await message.reply_text("لم أجد هذا المستخدم.")
    if user_id == BOT_ID: return await message.reply_text("لا يمكنني كتم نفسي.")
    if user_id in SUDOERS: return await message.reply_text("لا يمكن كتم مطور البوت.")
    if user_id in (await list_admins(message.chat.id)): return await message.reply_text("لا يمكن كتم مشرف.")
    mention = (await app.get_users(user_id)).mention
    keyboard = ikb({"🚨 إلغاء الكتم 🚨": f"unmute_{user_id}"})
    msg = f"**تم كتم:** {mention}\n**بواسطة:** {message.from_user.mention if message.from_user else 'مجهول'}\n"
    if message.command[0] == "tmute":
        split = reason.split(None, 1)
        time_value = split[0]
        temp_reason = split[1] if len(split) > 1 else ""
        until = await time_converter(message, time_value)
        msg += f"**المدة:** {time_value}\n**السبب:** {temp_reason}"
        await message.chat.restrict_member(user_id, permissions=ChatPermissions(), until_date=until)
    else:
        if reason: msg += f"**السبب:** {reason}"
        await message.chat.restrict_member(user_id, permissions=ChatPermissions())
    await message.reply_text(msg, reply_markup=keyboard)

# إلغاء كتم
@app.on_message(filters.command("unmute") & ~filters.private)
@adminsOnly("can_restrict_members")
async def unmute(_, message: Message):
    user_id = await extract_user(message)
    if not user_id: return await message.reply_text("لم أجد هذا المستخدم.")
    await message.chat.unban_member(user_id)
    await message.reply_text(f"تم إلغاء كتم {(await app.get_users(user_id)).mention}")

# حظر الحسابات المحذوفة
@app.on_message(filters.command("ban_ghosts") & ~filters.private)
@adminsOnly("can_restrict_members")
async def ban_deleted_accounts(_, message: Message):
    chat_id = message.chat.id
    deleted_users = []
    m = await message.reply("جارٍ البحث عن الحسابات المحذوفة...")
    async for i in app.get_chat_members(chat_id):
        if i.user.is_deleted:
            deleted_users.append(i.user.id)
    banned = 0
    for uid in deleted_users:
        try:
            await message.chat.ban_member(uid)
            banned += 1
        except: pass
    await m.edit(f"تم حظر {banned} حساباً محذوفاً.")

# تحذير
@app.on_message(filters.command(["warn", "dwarn"]) & ~filters.private)
@adminsOnly("can_restrict_members")
async def warn_user(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    if not user_id: return await message.reply_text("لم أجد هذا المستخدم.")
    if user_id == BOT_ID: return await message.reply_text("لا يمكنني تحذير نفسي.")
    if user_id in SUDOERS: return await message.reply_text("لا يمكن تحذير مطور البوت.")
    if user_id in (await list_admins(message.chat.id)): return await message.reply_text("لا يمكن تحذير مشرف.")
    user, warns = await asyncio.gather(app.get_users(user_id), get_warn(message.chat.id, await int_to_alpha(user_id)))
    warns = warns["warns"] if warns else 0
    if message.command[0][0] == "d": await message.reply_to_message.delete()
    if warns >= 2:  # 3 تحذيرات تؤدي إلى حظر
        await message.chat.ban_member(user_id)
        await message.reply_text(f"تجاوز {user.mention} عدد التحذيرات، تم حظره!")
        await remove_warns(message.chat.id, await int_to_alpha(user_id))
    else:
        new_warns = warns + 1
        await add_warn(message.chat.id, await int_to_alpha(user_id), {"warns": new_warns})
        msg = f"**تم تحذير:** {user.mention}\n**بواسطة:** {message.from_user.mention if message.from_user else 'مجهول'}\n**السبب:** {reason or 'بدون سبب'}\n**التحذيرات:** {new_warns}/3"
        keyboard = ikb({"🚨 إزالة تحذير 🚨": f"unwarn_{user_id}"})
        await message.reply_text(msg, reply_markup=keyboard)

@app.on_callback_query(filters.regex("unwarn_"))
async def remove_warning(_, cq: CallbackQuery):
    from_user = cq.from_user
    permissions = await member_permissions(cq.message.chat.id, from_user.id)
    if "can_restrict_members" not in permissions and from_user.id not in SUDOERS:
        return await cq.answer("ليس لديك صلاحية إزالة التحذيرات.", show_alert=True)
    user_id = cq.data.split("_")[1]
    warns = await get_warn(cq.message.chat.id, await int_to_alpha(user_id))
    if not warns or warns["warns"] == 0:
        return await cq.answer("لا يوجد تحذيرات لهذا المستخدم.")
    new_warns = warns["warns"] - 1
    await add_warn(cq.message.chat.id, await int_to_alpha(user_id), {"warns": new_warns})
    text = cq.message.text.markdown
    text = f"~~{text}~~\n\n__تم إزالة تحذير بواسطة {from_user.mention}__"
    await cq.message.edit(text)

# إزالة كل التحذيرات
@app.on_message(filters.command("rmwarns") & ~filters.private)
@adminsOnly("can_restrict_members")
async def remove_warnings(_, message: Message):
    if not message.reply_to_message: return await message.reply_text("الرد على رسالة المستخدم.")
    user_id = message.reply_to_message.from_user.id
    mention = message.reply_to_message.from_user.mention
    await remove_warns(message.chat.id, await int_to_alpha(user_id))
    await message.reply_text(f"تم إزالة جميع تحذيرات {mention}.")

# عرض التحذيرات
@app.on_message(filters.command("warns") & ~filters.private)
@capture_err
async def check_warns(_, message: Message):
    user_id = await extract_user(message)
    if not user_id: return await message.reply_text("لم أجد هذا المستخدم.")
    warns = await get_warn(message.chat.id, await int_to_alpha(user_id))
    warns = warns["warns"] if warns else 0
    mention = (await app.get_users(user_id)).mention
    await message.reply_text(f"{mention} لديه {warns}/3 تحذيرات.")

# الإبلاغ
@app.on_message((filters.command("report") | filters.command(["admins", "admin"], prefixes="@")) & ~filters.private)
@capture_err
async def report_user(_, message):
    if len(message.text.split()) <= 1 and not message.reply_to_message:
        return await message.reply_text("رد على رسالة العضو للإبلاغ عنه.")
    reply = message.reply_to_message or message
    reported_id = reply.from_user.id if reply.from_user else reply.sender_chat.id
    admins = await list_admins(message.chat.id)
    if reported_id in admins or reported_id == message.chat.id:
        return await message.reply_text("هذا العضو مشرف، لا يمكن الإبلاغ عنه.")
    mention = reply.from_user.mention if reply.from_user else reply.sender_chat.title
    text = f"تم الإبلاغ عن {mention} إلى المشرفين."
    async for admin in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        if not admin.user.is_bot and not admin.user.is_deleted:
            text += f"[\u2063](tg://user?id={admin.user.id})"
    await reply.reply_text(text)

# رابط الدعوة
@app.on_message(filters.command("invite") & ~filters.private)
@adminsOnly("can_invite_users")
async def invite(_, message):
    link = (await app.get_chat(message.chat.id)).invite_link
    if not link: link = await app.export_chat_invite_link(message.chat.id)
    await message.reply_text(f"رابط دعوة المجموعة:\n{link}", disable_web_page_preview=True)
