from wbb import db
notesdb = db.notes
filtersdb = db.filters
warnsdb = db.warns
karmadb = db.karma
welcomedb = db.welcome
locksdb = db.locks
gbansdb = db.gban

# هنا دوال عديدة موجودة في الكود الأصلي، سأعطي أمثلة:
async def get_filters_names(chat_id: int):
    data = await filtersdb.find_one({"chat_id": chat_id})
    return list(data["filters"].keys()) if data else []

async def save_filter(chat_id: int, name: str, _filter: dict):
    await filtersdb.update_one({"chat_id": chat_id}, {"$set": {f"filters.{name}": _filter}}, upsert=True)

async def delete_filter(chat_id: int, name: str):
    await filtersdb.update_one({"chat_id": chat_id}, {"$unset": {f"filters.{name}": ""}})

