from pyrogram.enums import ChatType, ParseMode
from pyrogram.filters import command
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from wbb import BOT_USERNAME, app

MARKDOWN = """
**📘 دليل التنسيق في البوت:**

يمكنك استخدام التنسيق التالي في رسائل الترحيب، الفلاتر، والملاحظات:

**المتغيرات:**
- `{name}` : اسم المستخدم
- `{chat}` : اسم المجموعة

**التنسيقات المدعومة:**
- `**نص غامق**` → **نص غامق**
- `__نص مائل__` → _نص مائل_
- `~~نص مشطوب~~` → ~~نص مشطوب~~
- `--تسطير--` → <u>تسطير</u>
- `` `كود` `` → `كود`
- `||مخفي||` → (مخفي)
- `[رابط](https://example.com)` → [رابط](https://example.com)

**إضافة أزرار:**
اكتب النص ثم `~` ثم الأزرار بهذا الشكل:
