"""Normalize and verify the CRM demo dataset used for end-to-end testing.

This startup seed is deliberately non-destructive for production data. It only
updates records already marked ``is_demo=True`` and creates missing demo
customers. The classic test naming is ``CUS-DEMO-001`` / ``Demo Customer 01``.
"""
from datetime import timedelta

from lib.db import db
from routers.common import new_id, now

CUSTOMER_COUNT = 15
INDUSTRIES = ["Manufacturing", "Oil & Gas", "Automation", "Food & Beverage", "Power Generation"]
CITIES = ["Jakarta", "Bekasi", "Cilegon", "Balikpapan", "Surabaya"]
POSITIONS = ["Procurement", "Engineering", "Maintenance", "Project", "Director"]


async def _sales_users() -> list[dict]:
    return await db.users.find(
        {"role": "SALES", "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]}},
        {"_id": 0, "id": 1, "name": 1},
    ).sort("name", 1).to_list(100)


async def _normalize_customers(sales: list[dict]) -> dict[str, str]:
    demo = await db.customers.find({"is_demo": True}, {"_id": 0}).to_list(1000)
    by_id = {str(x.get("customer_id")): x for x in demo if x.get("customer_id")}
    legacy = [x for x in demo if str(x.get("customer_id", "")).startswith("DEMO-CUS-")]
    legacy.sort(key=lambda x: str(x.get("customer_id")))
    result: dict[str, str] = {}

    for index in range(1, CUSTOMER_COUNT + 1):
        customer_id = f"CUS-DEMO-{index:03d}"
        name = f"Demo Customer {index:02d}"
        industry = INDUSTRIES[(index - 1) % len(INDUSTRIES)]
        city = CITIES[(index - 1) % len(CITIES)]
        pic = f"PIC Demo {index:02d}"
        position = POSITIONS[(index - 1) % len(POSITIONS)]
        doc = by_id.get(customer_id)
        if doc is None and index >= 11 and legacy:
            doc = legacy.pop(0)

        if doc is None:
            owner = sales[(index - 1) % len(sales)]
            doc = {
                "id": new_id(), "customer_id": customer_id, "name": name,
                "company_name": f"PT Demo Industri {index:02d}", "company": f"PT Demo Industri {index:02d}",
                "industry": industry, "city": city, "province": "DKI Jakarta" if city == "Jakarta" else "",
                "phone": f"021555{index:04d}", "email": f"customer{index:02d}@crm-demo.local",
                "pic_name": pic, "pic_position": position, "source": "Dummy Data", "status": "Active",
                "sales_id": owner["id"], "sales_name": owner["name"],
                "address": f"Jl. Demo Industri No. {index}, {city}",
                "notes": "Demo record for CRM module verification.", "is_demo": True,
                "demo_label": "CRM UI demo data", "created_at": now() - timedelta(days=index), "updated_at": now(),
            }
            await db.customers.insert_one(doc)
        else:
            owner = sales[(index - 1) % len(sales)]
            await db.customers.update_one(
                {"id": doc["id"]},
                {"$set": {
                    "customer_id": customer_id, "name": name,
                    "company_name": f"PT Demo Industri {index:02d}", "company": f"PT Demo Industri {index:02d}",
                    "industry": industry, "city": city, "province": "DKI Jakarta" if city == "Jakarta" else "",
                    "phone": f"021555{index:04d}", "email": f"customer{index:02d}@crm-demo.local",
                    "pic_name": pic, "pic_position": position, "source": "Dummy Data", "status": "Active",
                    "sales_id": owner["id"], "sales_name": owner["name"],
                    "address": f"Jl. Demo Industri No. {index}, {city}",
                    "notes": "Demo record for CRM module verification.", "is_demo": True,
                    "demo_label": "CRM UI demo data", "updated_at": now(),
                }},
            )
        result[customer_id] = str(doc["id"])

    return result


async def _sync_customer_names(customer_ids: dict[str, str]) -> None:
    names = {internal_id: f"Demo Customer {int(customer_id[-3:]):02d}" for customer_id, internal_id in customer_ids.items()}
    for collection in ["opportunities", "quotations", "purchase_orders", "activities"]:
        for internal_id, name in names.items():
            await db[collection].update_many(
                {"is_demo": True, "customer_id": internal_id},
                {"$set": {"customer_name": name, "updated_at": now()}},
            )

    legacy_names = {
        11: "PT Nusantara Petro Energy", 12: "PT Garuda Industrial Systems",
        13: "PT Prima Power Generation", 14: "PT Samudra Petrochemical",
        15: "PT Mitra Automation Integrasi",
    }
    for number, old_name in legacy_names.items():
        await db.tasks.update_many(
            {"is_demo": True, "customer_name": old_name},
            {"$set": {"customer_name": f"Demo Customer {number:02d}", "updated_at": now()}},
        )

    for internal_id, name in names.items():
        await db.contacts.update_many(
            {"is_demo": True, "customer_id": internal_id},
            {"$set": {"customer_name": name, "updated_at": now()}},
        )
        await db.leads.update_many(
            {"is_demo": True, "customer_id": internal_id},
            {"$set": {"company": f"PT Demo Industri {int(name[-2:]):02d}", "updated_at": now()}},
        )


async def _verify_demo_dataset() -> None:
    collections = [
        "customers", "contacts", "leads", "products", "opportunities", "activities",
        "quotations", "purchase_orders", "tasks", "sales_targets",
    ]
    counts = {collection: await db[collection].count_documents({"is_demo": True}) for collection in collections}
    stage_values = await db.opportunities.distinct("stage", {"is_demo": True})
    quotation_values = await db.quotations.distinct("status", {"is_demo": True})
    order_values = await db.purchase_orders.distinct("status", {"is_demo": True})
    activity_values = await db.activities.distinct("activity_type", {"is_demo": True})
    print(
        "CRM demo verification | counts=%s | pipeline=%s | quotations=%s | orders=%s | activities=%s",
        counts,
        sorted(str(x) for x in stage_values),
        sorted(str(x) for x in quotation_values),
        sorted(str(x) for x in order_values),
        sorted(str(x) for x in activity_values),
    )


async def seed_demo_data():
    sales = await _sales_users()
    if not sales:
        print("CRM demo seed skipped: no active SALES user found")
        return
    customer_ids = await _normalize_customers(sales)
    if len(customer_ids) != CUSTOMER_COUNT:
        print("CRM demo seed incomplete: expected 15 demo customers, prepared %s", len(customer_ids))
        return
    await _sync_customer_names(customer_ids)
    await _verify_demo_dataset()
