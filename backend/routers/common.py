from datetime import datetime, timezone
from typing import Any
import uuid
from pymongo import ReturnDocument
from lib.db import db


def now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


async def audit(user: dict, action: str, module: str, record_id: str | None = None, changes: dict[str, Any] | None = None):
    await db.audit_logs.insert_one({"id": new_id(), "user_name": user.get("name", "System"), "action": action, "module": module, "record_id": record_id, "changes": changes, "created_at": now()})


async def next_number(collection: str, prefix: str) -> str:
    year = now().year
    counter = await db.number_sequences.find_one_and_update({"key": f"{prefix}-{year}"}, {"$inc": {"value": 1}}, upsert=True, return_document=ReturnDocument.AFTER)
    return f"{prefix}-{year}-{counter['value']:05d}"


async def page_collection(collection: str, page: int, page_size: int, search: str = "", filters: dict | None = None):
    query: dict = filters.copy() if filters else {}
    if search:
        query["$or"] = [{field: {"$regex": search, "$options": "i"}} for field in ["name", "customer_name", "email", "subject", "code", "number", "po_number", "opportunity_id"]]
    total = await db[collection].count_documents(query)
    items = await db[collection].find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size).to_list(page_size)
    for item in items:
        item.pop("_id", None)
        item.pop("password_hash", None)
        item.pop("content", None)
        item.pop("token", None)
    return {"items": items, "page": page, "page_size": page_size, "total": total}