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
