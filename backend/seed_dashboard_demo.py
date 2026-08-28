"""Idempotently fills only empty dashboard source collections with clearly marked demo data."""

import asyncio
from datetime import date, timedelta

from lib.db import client, db
from routers.common import new_id, now


async def seed_empty_dashboard_sources():
    customers = await db.customers.find({}, {"_id": 0, "id": 1, "name": 1}).limit(20).to_list(20)
    if not customers:
        raise RuntimeError("Customers collection is empty; run the primary CRM seed first")

    if await db.contacts.count_documents({}) == 0:
        await db.contacts.insert_many([
            {"id": new_id(), "contact_id": f"CON-DEMO-{index + 1:04d}", "customer_id": customer["id"], "customer_name": customer["name"], "first_name": f"Demo Contact {index + 1}", "last_name": "Industrial", "position": "Procurement", "department": "Supply Chain", "email": f"demo.contact{index + 1}@example.co.id", "mobile": f"+62 812 9000 {index + 1:04d}", "contact_type": "Procurement", "is_decision_maker": index % 3 == 0, "status": "Active", "sales_id": "sales-0001", "sales_name": "Budi Santoso", "is_demo": True, "demo_label": "Dashboard demo data", "created_at": now() - timedelta(days=index)}
            for index, customer in enumerate(customers)
        ])

    if await db.leads.count_documents({}) == 0:
        await db.leads.insert_many([
            {"id": new_id(), "lead_number": f"LEAD-DEMO-{index + 1:04d}", "lead_date": (date.today() - timedelta(days=index * 2)).isoformat(), "company": customer["name"], "customer_id": customer["id"], "source": "Website" if index % 2 == 0 else "Referral", "industry": "Industrial Automation", "product_interest": "PLC & Industrial Network", "estimated_value": 150_000_000 + index * 25_000_000, "currency": "IDR", "probability": 25 + (index % 4) * 10, "status": ["New", "Contacted", "Qualified"][index % 3], "sales_id": "sales-0001", "sales_name": "Budi Santoso", "is_demo": True, "demo_label": "Dashboard demo data", "created_at": now() - timedelta(days=index * 2)}
            for index, customer in enumerate(customers[:12])
        ])

    if await db.sales_targets.count_documents({}) == 0:
        await db.sales_targets.insert_many([
            {"id": new_id(), "year": now().year, "month": month, "sales_id": "sales-0001", "sales_name": "Budi Santoso", "team": "Industrial Sales", "target": 750_000_000, "currency": "IDR", "is_demo": True, "demo_label": "Dashboard demo data", "created_at": now()}
            for month in range(1, 13)
        ])

    for collection, field in [("contacts", "customer_id"), ("leads", "sales_id"), ("sales_targets", "year")]:
        await db[collection].create_index(field)

    for collection, field in [("contacts", "customer_id"), ("leads", "sales_id"), ("sales_targets", "year")]:
        await db[collection].create_index(field)
    print("Dashboard demo sources ready; existing records were not overwritten")


if __name__ == "__main__":
    asyncio.run(seed_empty_dashboard_sources())
    client.close()