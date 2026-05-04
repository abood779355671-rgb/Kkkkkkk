"""
MIT License - مترجم للعربية
نظام الكارما (التقييم)
"""
import re
from pyrogram import filters
from wbb import app
from wbb.core.decorators.errors import capture_err
from wbb.core.decorators.permissions import adminsOnly
from wbb.core.sections import section
from wbb.utils.dbfunctions import (alpha_to_int, get_karma, get_karmas, int_to_alpha, is_karma_on,
                                   karma_off, karma_on, update_karma)
from wbb.utils.filter_groups import karma_positive_group, karma_negative_group
from wbb.utils.functions import get_specific_usernames

__MODULE__ = "الكارما"
__HELP__ = """
**نظام التقييم (كارما):**
- استخدم الكلمات: + , +1 , شكراً , 👍 للإعجاب برسالة.
- استخدم الكلمات: - , -1 , سيء , 👎 لعدم الإعجاب.

/karma_toggle [تفعيل|تعطيل] - تفعيل أو تعطيل نظام الكارما في الدردشة.
رد على رسالة بـ /karma لعرض كارما المستخدم.
/karma بدون رد لعرض أعلى 10 كارما في الدردشة.
"""

regex_upvote = r"^(\++|\+1|شكراً|شكرا|ثانكس|thank|thanks|👍|جميل|رائع|جيد)$"
regex_downvote = r"^(-+|-1|سيء|سيئ|رديء|👎|غير جيد)$"

@app.on_message(filters.text & filters.group & filters.incoming & filters.reply & filters.regex(regex_upvote, re.IGNORECASE) & ~filters.via_bot & ~filters.bot, group=karma_positive_group)
@capture_err
async def upvote(_, message):
    if not await is_karma_on(message.chat.id):
        return
    if not message.reply_to_message.from_user or not message.from_user:
        return
    if message.reply_to_message.from_user.id == message.from_user.id:
        return
    chat_id = message.chat.id
    target_id = message.reply_to_message.from_user.id
    current = await get_karma(chat_id, await int_to_alpha(target_id))
    karma = current["karma"] + 1 if current else 1
    await update_karma(chat_id, await int_to_alpha(target_id), {"karma": karma})
    await message.reply_text(f"⭐ زادت كارما {message.reply_to_message.from_user.mention} إلى {karma}")

@app.on_message(filters.text & filters.group & filters.incoming & filters.reply & filters.regex(regex_downvote, re.IGNORECASE) & ~filters.via_bot & ~filters.bot, group=karma_negative_group)
@capture_err
async def downvote(_, message):
    if not await is_karma_on(message.chat.id):
        return
    if not message.reply_to_message.from_user or not message.from_user:
        return
    if message.reply_to_message.from_user.id == message.from_user.id:
        return
    chat_id = message.chat.id
    target_id = message.reply_to_message.from_user.id
    current = await get_karma(chat_id, await int_to_alpha(target_id))
    karma = current["karma"] - 1 if current else -1
    await update_karma(chat_id, await int_to_alpha(target_id), {"karma": karma})
    await message.reply_text(f"🌟 نقصت كارما {message.reply_to_message.from_user.mention} إلى {karma}")

@app.on_message(filters.command("karma") & filters.group)
@capture_err
async def command_karma(_, message):
    chat_id = message.chat.id
    if not message.reply_to_message:
        karmas = await get_karmas(chat_id)
        if not karmas:
            return await message.reply_text("لا توجد بيانات كارما في هذه الدردشة.")
        # ترتيب تنازلي
        sorted_karma = sorted(karmas.items(), key=lambda x: x[1]["karma"], reverse=True)[:10]
        if not sorted_karma:
            return await message.reply_text("لا توجد كارما إيجابية.")
        user_ids = []
        for alpha, val in sorted_karma:
            try:
                uid = await alpha_to_int(alpha)
                user_ids.append(uid)
            except:
                continue
        user_info = await get_specific_usernames(app, user_ids)
        text = f"**🏆 قائمة الكارما في {message.chat.title}:**\n"
        for alpha, val in sorted_karma:
            uid = await alpha_to_int(alpha)
            name = user_info.get(uid, f"مستخدم {uid}")
            text += f"• `{name}` : **{val['karma']}**\n"
        await message.reply_text(text)
    else:
        target_id = message.reply_to_message.from_user.id
        if not target_id:
            return await message.reply_text("لا يمكن عرض كارما مستخدم مجهول.")
        karma = await get_karma(chat_id, await int_to_alpha(target_id))
        points = karma["karma"] if karma else 0
        await message.reply_text(f"**كارما {message.reply_to_message.from_user.mention}:** `{points}`")

@app.on_message(filters.command("karma_toggle") & ~filters.private)
@adminsOnly("can_change_info")
async def toggle_karma(_, message):
    if len(message.command) != 2:
        return await message.reply_text("**الاستخدام:** /karma_toggle [تفعيل|تعطيل]")
    state = message.command[1].lower()
    if state == "تفعيل":
        await karma_on(message.chat.id)
        await message.reply_text("✅ تم تفعيل نظام الكارما في هذه الدردشة.")
    elif state == "تعطيل":
        await karma_off(message.chat.id)
        await message.reply_text("❌ تم تعطيل نظام الكارما.")
    else:
        await message.reply_text("خيار غير صالح، استخدم `تفعيل` أو `تعطيل`.")
