"""Idempotent production demo data for UI/module verification.

Adds a small, clearly marked demo dataset without modifying or deleting
existing CRM records. Safe to run on every application startup.
"""
from datetime import date, timedelta
from passlib.context import CryptContext

from lib.db import db
from routers.common import new_id, now

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEMO_USERS = [
    {
        "id": "demo-user-manager-2026",
        "user_id": "USR-DEMO-001",
        "name": "Dina Pratama",
        "email": "dina.demo@crm.co.id",
        "role": "SALES_MANAGER",
        "phone": "+62 811 9000 1001",
        "status": "Active",
    },
    {
        "id": "demo-user-sales-2026-01",
        "user_id": "USR-DEMO-002",
        "name": "Andi Wijaya",
        "email": "andi.demo@crm.co.id",
        "role": "SALES",
        "manager_id": "demo-user-manager-2026",
        "phone": "+62 811 9000 1002",
        "status": "Active",
    },
    {
        "id": "demo-user-sales-2026-02",
        "user_id": "USR-DEMO-003",
        "name": "Sari Lestari",
        "email": "sari.demo@crm.co.id",
        "role": "SALES",
        "manager_id": "demo-user-manager-2026",
        "phone": "+62 811 9000 1003",
        "status": "Active",
    },
]

DEMO_CUSTOMERS = [
    ("DEMO-CUS-001", "PT Nusantara Petro Energy", "Oil & Gas", "Balikpapan", "Rizky Hidayat", "Procurement Manager", "Andi Wijaya"),
    ("DEMO-CUS-002", "PT Garuda Industrial Systems", "Manufacturing", "Jakarta", "Maya Putri", "Engineering Manager", "Sari Lestari"),
    ("DEMO-CUS-003", "PT Prima Power Generation", "Power Generation", "Cilegon", "Bambang Setiawan", "Project Manager", "Andi Wijaya"),
    ("DEMO-CUS-004", "PT Samudra Petrochemical", "Petrochemical", "Cilacap", "Dewi Anggraini", "Maintenance Manager", "Sari Lestari"),
    ("DEMO-CUS-005", "PT Mitra Automation Integrasi", "System Integrator", "Jakarta", "Fajar Nugroho", "Director", "Andi Wijaya"),
]

DEMO_OPPORTUNITIES = [
    ("DEMO-OPP-001", "Fuel Gas Heater Package", "DEMO-CUS-001", "PT Nusantara Petro Energy", "Andi Wijaya", 850_000_000, 60, "Proposal", "Watlow", "Electric Heater"),
    ("DEMO-OPP-002", "Industrial PC Modernization", "DEMO-CUS-002", "PT Garuda Industrial Systems", "Sari Lestari", 425_000_000, 40, "Qualification", "Axiomtek", "Industrial PC"),
    ("DEMO-OPP-003", "Power Control Upgrade", "DEMO-CUS-003", "PT Prima Power Generation", "Andi Wijaya", 675_000_000, 70, "Negotiation", "Eurotherm", "Epack"),
    ("DEMO-OPP-004", "Process Temperature Monitoring", "DEMO-CUS-004", "PT Samudra Petrochemical", "Sari Lestari", 310_000_000, 20, "Lead", "Watlow", "Temperature Controller"),
    ("DEMO-OPP-005", "Remote I/O & Industrial Network", "DEMO-CUS-005", "PT Mitra Automation Integrasi", "Andi Wijaya", 195_000_000, 100, "Won", "ICP DAS", "Remote I/O"),
]


async def seed_demo_data():
    # Users: add exactly these three demo users if they do not already exist.
    for base in DEMO_USERS:
        if await db.users.find_one({"id": base["id"]}):
            continue
        doc = {
            **base,
            "password_hash": pwd.hash("Demo@12345"),
            "is_demo": True,
            "demo_label": "CRM UI demo data",
            "created_at": now(),
        }
        await db.users.insert_one(doc)

    # Customers: stable IDs make this operation idempotent.
    customer_ids = {}
    for index, (customer_id, name, industry, city, pic, position, sales_name) in enumerate(DEMO_CUSTOMERS):
        existing = await db.customers.find_one({"customer_id": customer_id})
        if existing:
            customer_ids[customer_id] = existing["id"]
            continue

        sales = await db.users.find_one({"name": sales_name, "is_demo": True})
        doc = {
            "id": new_id(),
            "customer_id": customer_id,
            "name": name,
            "company_name": name,
            "company": name,
            "industry": industry,
            "city": city,
            "province": "DKI Jakarta" if city == "Jakarta" else "",
            "phone": "+62 21 7000 1000",
            "email": f"{customer_id.lower()}@demo.co.id",
            "pic_name": pic,
            "pic_position": position,
            "source": "Demo / UI Testing",
            "status": "Active",
            "sales_id": sales["id"] if sales else None,
            "sales_name": sales_name,
            "address": f"Kawasan Industri {city}",
            "notes": "Demo record for CRM module verification.",
            "is_demo": True,
            "demo_label": "CRM UI demo data",
            "created_at": now() - timedelta(days=index + 1),
            "updated_at": now(),
        }
        await db.customers.insert_one(doc)
        customer_ids[customer_id] = doc["id"]

    # Opportunities: five records distributed across Pipeline stages.
    for index, (opp_id, name, customer_id, customer_name, sales_name, value, probability, stage, brand, product) in enumerate(DEMO_OPPORTUNITIES):
        if await db.opportunities.find_one({"opportunity_id": opp_id}):
            continue
        sales = await db.users.find_one({"name": sales_name, "is_demo": True})
        customer_ref = customer_ids.get(customer_id)
        doc = {
            "id": new_id(),
            "opportunity_id": opp_id,
            "name": name,
            "customer_id": customer_ref or customer_id,
            "customer_name": customer_name,
            "sales_id": sales["id"] if sales else None,
            "sales_name": sales_name,
            "value": value,
            "probability": probability,
            "stage": stage,
            "target_close": (date.today() + timedelta(days=15 + index * 12)).isoformat(),
            "brand": brand,
            "product": product,
            "next_action": "Follow up customer requirement and commercial proposal",
            "description": "Demo opportunity for Sales Pipeline UI verification.",
            "is_demo": True,
            "demo_label": "CRM UI demo data",
            "created_at": now() - timedelta(days=index + 2),
            "updated_at": now(),
        }
        await db.opportunities.insert_one(doc)

    print("CRM demo data ready: 5 customers, 5 pipeline opportunities, 3 users")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_demo_data())
