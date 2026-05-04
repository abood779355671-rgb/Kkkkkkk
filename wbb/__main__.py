import asyncio
import importlib
import re
from contextlib import closing, suppress

from pyrogram import filters, idle
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from uvloop import install

from wbb import BOT_NAME, BOT_USERNAME, LOG_GROUP_ID, USERBOT_NAME, aiohttpsession, app, log
from wbb.core.keyboard import ikb
from wbb.modules import ALL_MODULES
from wbb.modules.sudoers import bot_sys_stats
from wbb.utils import paginate_modules
from wbb.utils.constants import MARKDOWN
from wbb.utils.dbfunctions import clean_restart_stage, get_rules
from wbb.utils.functions import extract_text_and_keyb

loop = asyncio.get_event_loop()
HELPABLE = {}

async def start_bot():
    global HELPABLE
    for module in ALL_MODULES:
        imported_module = importlib.import_module("wbb.modules." + module)
        if hasattr(imported_module, "__MODULE__") and imported_module.__MODULE__:
            imported_module.__MODULE__ = imported_module.__MODULE__
            if hasattr(imported_module, "__HELP__") and imported_module.__HELP__:
                HELPABLE[imported_module.__MODULE__.replace(" ", "_").lower()] = imported_module
    log.info(f"البوت {BOT_NAME} يعمل الآن!")
    log.info(f"بوت المستخدم {USERBOT_NAME} يعمل الآن!")
    restart_data = await clean_restart_stage()
    try:
        if restart_data:
            await app.edit_message_text(restart_data["chat_id"], restart_data["message_id"], "**تمت إعادة التشغيل بنجاح**")
        else:
            await app.send_message(LOG_GROUP_ID, "تم تشغيل البوت!")
    except Exception:
        pass
    await idle()
    await aiohttpsession.close()
    await app.stop()
    for task in asyncio.all_tasks():
        task.cancel()

home_keyboard_pm = InlineKeyboardMarkup([
    [InlineKeyboardButton("الأوامر ❓", callback_data="bot_commands"),
     InlineKeyboardButton("المستودع 🛠", url="https://github.com/thehamkercat/WilliamButcherBot")],
    [InlineKeyboardButton("إحصائيات النظام 🖥", callback_data="stats_callback"),
     InlineKeyboardButton("الدعم 👨", url="http://t.me/WBBSupport")],
    [InlineKeyboardButton("أضفني إلى مجموعتك 🎉", url=f"http://t.me/{BOT_USERNAME}?startgroup=new")]
])
home_text_pm = f"مرحباً! أنا {BOT_NAME}. يمكنني إدارة مجموعتك بميزات كثيرة، أضفني إلى مجموعتك."

keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("المساعدة ❓", url=f"t.me/{BOT_USERNAME}?start=help"),
     InlineKeyboardButton("المستودع 🛠", url="https://github.com/thehamkercat/WilliamButcherBot")],
    [InlineKeyboardButton("إحصائيات النظام 💻", callback_data="stats_callback"),
     InlineKeyboardButton("الدعم 👨", url="t.me/WBBSupport")]
])

@app.on_message(filters.command("start"))
async def start(_, message):
    if message.chat.type != ChatType.PRIVATE:
        return await message.reply("أرسل لي في الخاص للمساعدة.", reply_markup=keyboard)
    if len(message.text.split()) > 1:
        name = (message.text.split(None, 1)[1]).lower()
        if name == "help":
            text, keyb = await help_parser(message.from_user.first_name)
            await message.reply(text, reply_markup=keyb)
        else:
            await message.reply(home_text_pm, reply_markup=home_keyboard_pm)
    else:
        await message.reply(home_text_pm, reply_markup=home_keyboard_pm)

@app.on_message(filters.command("help"))
async def help_command(_, message):
    if message.chat.type != ChatType.PRIVATE:
        await message.reply("أرسل لي في الخاص لعرض المساعدة.", reply_markup=keyboard)
    else:
        text, help_keyboard = await help_parser(message.from_user.first_name)
        await message.reply(text, reply_markup=help_keyboard, disable_web_page_preview=True)

async def help_parser(name, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    return (f"مرحباً {name}، أنا {BOT_NAME}\nبوت لإدارة المجموعات. اختر أحد الأقسام أدناه.", keyboard)

@app.on_callback_query(filters.regex("stats_callback"))
async def stats_callbacc(_, CallbackQuery):
    text = await bot_sys_stats()
    await app.answer_callback_query(CallbackQuery.id, text, show_alert=True)

if __name__ == "__main__":
    install()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(start_bot())
        loop.run_until_complete(asyncio.sleep(3.0))
