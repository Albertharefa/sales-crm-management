"""One-time cleanup of seeded demo CRM data.

This temporary deployment cleanup removes only records explicitly marked as
 demo or matching the known seeded demo customer IDs/names. It never removes
normal live CRM customer records.
"""
from lib.db import db


async def seed_demo_data():
    customer_filter = {
        "$or": [
            {"is_demo": True},
            {"id": {"$regex": r"^(DEMO-CUS-|CUS-DEMO-)"}},
            {"customer_id": {"$regex": r"^(DEMO-CUS-|CUS-DEMO-)"}},
        ]
    }
    customers = await db.customers.find(customer_filter, {"_id": 0, "id": 1, "customer_id": 1}).to_list(5000)
    ids = {str(item.get("id")) for item in customers if item.get("id")}
    ids.update(str(item.get("customer_id")) for item in customers if item.get("customer_id"))

    deleted = {}
    if ids:
        result = await db.customers.delete_many({"$or": [{"id": {"$in": list(ids)}}, {"customer_id": {"$in": list(ids)}}]})
        deleted["customers"] = int(result.deleted_count)

        # Remove only demo-linked transactional records, preserving live CRM data.
        for collection in ["contacts", "leads", "opportunities", "quotations", "purchase_orders", "activities", "tasks", "projects", "tenders", "documents"]:
            result = await db[collection].delete_many({"$or": [{"customer_id": {"$in": list(ids)}}, {"customer_ids": {"$in": list(ids)}}]})
            if result.deleted_count:
                deleted[collection] = int(result.deleted_count)

    # Also remove records explicitly marked demo in operational collections.
    for collection in ["contacts", "leads", "opportunities", "quotations", "purchase_orders", "activities", "tasks", "projects", "tenders", "documents", "sales_targets"]:
        result = await db[collection].delete_many({"is_demo": True})
        if result.deleted_count:
            deleted[f"{collection}_demo"] = int(result.deleted_count)

    print(f"One-time demo cleanup complete: {deleted}")
