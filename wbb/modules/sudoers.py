"""
MIT License - مترجم للعربية
أوامر خاصة بالمطورين (sudoers)
"""
import asyncio
import os
import subprocess
import time
import psutil
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait
from wbb import (BOT_ID, GBAN_LOG_GROUP_ID, SUDOERS, USERBOT_USERNAME, app, bot_start_time)
from wbb.core.decorators.errors import capture_err
from wbb.utils import formatter
from wbb.utils.dbfunctions import (add_gban_user, get_served_chats, get_served_users, is_gbanned_user, remove_gban_user)
from wbb.utils.functions import extract_user, extract_user_and_reason, restart

__MODULE__ = "المطورين"
__HELP__ = """
**أوامر المطورين فقط:**

/stats - إحصائيات النظام.
/gstats - إحصائيات البوت العالمية.
/gban - حظر مستخدم عالمياً في كل المجموعات.
/ungban - إلغاء الحظر العالمي.
/clean_db - تنظيف قاعدة البيانات (إزالة الدردشات التي غادرها البوت).
/broadcast - إرسال رسالة إلى كل المجموعات التي فيها البوت.
/ubroadcast - إرسال رسالة إلى كل المستخدمين الذين تفاعلوا مع البوت.
/update - تحديث البوت من GitHub وإعادة التشغيل.
/restart - إعادة تشغيل البوت.
/eval - تنفيذ كود بايثون (يُستخدم في الخاص فقط).
/sh - تنفيذ أوامر شيل (shell).
"""

async def bot_sys_stats():
    uptime = int(time.time() - bot_start_time)
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    proc = psutil.Process(os.getpid())
    stats = f"""
**إحصائيات {USERBOT_USERNAME}** :
- وقت التشغيل: {formatter.get_readable_time(uptime)}
- ذاكرة البوت: {round(proc.memory_info()[0] / 1024 ** 2)} MB
- استخدام المعالج: {cpu}%
- استخدام الرام: {mem}%
- استخدام القرص: {disk}%
"""
    return stats

@app.on_message(filters.command("stats") & SUDOERS)
@capture_err
async def stats_cmd(_, message):
    text = await bot_sys_stats()
    await message.reply_text(text)

@app.on_message(filters.command("gban") & SUDOERS)
@capture_err
async def gban(_, message):
    user_id, reason = await extract_user_and_reason(message)
    if not user_id or not reason:
        return await message.reply_text("**الاستخدام:** /gban [معرف/رد] [السبب]")
    user = await app.get_users(user_id)
    if user_id in SUDOERS or user_id == BOT_ID:
        return await message.reply_text("لا يمكن حظر مطور أو البوت نفسه.")
    if await is_gbanned_user(user_id):
        return await message.reply_text("هذا المستخدم محظور عالمياً بالفعل.")
    served_chats = await get_served_chats()
    m = await message.reply_text(f"**جاري الحظر العالمي لـ {user.mention}...** سيطول {len(served_chats)} ثانية.")
    await add_gban_user(user_id)
    count = 0
    for chat in served_chats:
        try:
            member = await app.get_chat_member(chat["chat_id"], user_id)
            if member.status == ChatMemberStatus.MEMBER:
                await app.ban_chat_member(chat["chat_id"], user_id)
                count += 1
            await asyncio.sleep(0.5)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except:
            pass
    try:
        await app.send_message(user_id, f"🚫 تم حظرك عالمياً بواسطة {message.from_user.mention}\nالسبب: {reason}")
    except:
        pass
    await m.edit(f"✅ تم حظر {user.mention} عالمياً في {count} مجموعة.")
    log_text = f"**حظر عالمي**\nمن: {message.from_user.mention}\nالمستخدم: {user.mention}\nالسبب: {reason}\nعدد المجموعات: {count}"
    await app.send_message(GBAN_LOG_GROUP_ID, log_text)

@app.on_message(filters.command("ungban") & SUDOERS)
@capture_err
async def ungban(_, message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("أرسل معرف المستخدم.")
    if not await is_gbanned_user(user_id):
        return await message.reply_text("هذا المستخدم غير محظور عالمياً.")
    await remove_gban_user(user_id)
    await message.reply_text(f"✅ تم إلغاء الحظر العالمي عن {(await app.get_users(user_id)).mention}")

@app.on_message(filters.command("broadcast") & SUDOERS)
@capture_err
async def broadcast(_, message):
    if not message.reply_to_message:
        return await message.reply_text("رد على رسالة لنشرها.")
    sent = 0
    chats = await get_served_chats()
    m = await message.reply_text("جاري النشر...")
    for chat in chats:
        try:
            await message.reply_to_message.copy(chat["chat_id"])
            sent += 1
            await asyncio.sleep(0.1)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except:
            pass
    await m.edit(f"📢 تم النشر إلى {sent} مجموعة.")

@app.on_message(filters.command("ubroadcast") & SUDOERS)
@capture_err
async def ubroadcast(_, message):
    if not message.reply_to_message:
        return await message.reply_text("رد على رسالة لنشرها للمستخدمين.")
    sent = 0
    users = await get_served_users()
    m = await message.reply_text("جاري النشر للمستخدمين...")
    for user in users:
        try:
            await message.reply_to_message.copy(user["user_id"])
            sent += 1
            await asyncio.sleep(0.1)
        except:
            pass
    await m.edit(f"📢 تم النشر إلى {sent} مستخدم.")

@app.on_message(filters.command("update") & SUDOERS)
async def update_restart(_, message):
    try:
        out = subprocess.check_output(["git", "pull"]).decode()
        if "Already up to date." in out:
            return await message.reply_text("✅ البوت محدث بالفعل.")
        await message.reply_text(f"```{out}```")
    except Exception as e:
        return await message.reply_text(str(e))
    m = await message.reply_text("🔄 تم التحديث، جاري إعادة التشغيل...")
    await restart(m)

@app.on_message(filters.command("restart") & SUDOERS)
async def restart_bot(_, message):
    m = await message.reply_text("🔄 جاري إعادة التشغيل...")
    await restart(m)

@app.on_message(filters.command("clean_db") & SUDOERS)
@capture_err
async def clean_db(_, message):
    m = await message.reply_text("🧹 جاري تنظيف قاعدة البيانات...")
    from wbb.utils.dbfunctions import remove_served_chat, get_served_chats
    chats = await get_served_chats()
    removed = 0
    for chat in chats:
        try:
            await app.get_chat(chat["chat_id"])
        except:
            await remove_served_chat(chat["chat_id"])
            removed += 1
    await m.edit(f"✅ تم تنظيف {removed} دردشة غير صالحة.")
