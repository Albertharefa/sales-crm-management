"""Idempotent production demo data for UI/module verification.

Adds a small, clearly marked demo dataset without modifying or deleting
existing CRM records. Safe to run on every application startup.
"""
from datetime import date, timedelta
from passlib.context import CryptContext

from lib.db import db
from routers.common import new_id, now, next_number

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


DEMO_QUOTATIONS = [
    ("DEMO-QT-001", "DEMO-CUS-001", "PT Nusantara Petro Energy", "Andi Wijaya", "Fuel Gas Heater Package - Budgetary", "Draft", 850_000_000, 1, 850_000_000),
    ("DEMO-QT-002", "DEMO-CUS-002", "PT Garuda Industrial Systems", "Sari Lestari", "Industrial PC Modernization Proposal", "Sent", 425_000_000, 1, 425_000_000),
    ("DEMO-QT-003", "DEMO-CUS-003", "PT Prima Power Generation", "Andi Wijaya", "Power Control Upgrade", "Negotiation", 675_000_000, 1, 675_000_000),
    ("DEMO-QT-004", "DEMO-CUS-004", "PT Samudra Petrochemical", "Sari Lestari", "Process Temperature Monitoring", "Approved", 310_000_000, 2, 155_000_000),
    ("DEMO-QT-005", "DEMO-CUS-005", "PT Mitra Automation Integrasi", "Andi Wijaya", "Remote I/O & Industrial Network", "Converted", 195_000_000, 1, 195_000_000),
    ("DEMO-QT-006", "DEMO-CUS-001", "PT Nusantara Petro Energy", "Andi Wijaya", "Electric Heater Replacement", "Rejected", 275_000_000, 1, 275_000_000),
    ("DEMO-QT-007", "DEMO-CUS-002", "PT Garuda Industrial Systems", "Sari Lestari", "Industrial Network Expansion", "Expired", 185_000_000, 5, 37_000_000),
    ("DEMO-QT-008", "DEMO-CUS-003", "PT Prima Power Generation", "Andi Wijaya", "Epack Power Controller", "Draft", 240_000_000, 2, 120_000_000),
    ("DEMO-QT-009", "DEMO-CUS-004", "PT Samudra Petrochemical", "Sari Lestari", "Temperature Controller Upgrade", "Sent", 165_000_000, 3, 55_000_000),
    ("DEMO-QT-010", "DEMO-CUS-005", "PT Mitra Automation Integrasi", "Andi Wijaya", "Remote I/O Solution Package", "Negotiation", 360_000_000, 4, 90_000_000),
]


DEMO_ACTIVITIES = [
    ("DEMO-ACT-001", "Customer Visit - PT Nusantara Petro Energy", "Call", 0, 5, "DEMO-CUS-001", "Andi Wijaya", "Open"),
    ("DEMO-ACT-002", "Technical Discussion - Industrial PC Requirement", "Meeting", 0, 7, "DEMO-CUS-002", "Sari Lestari", "Open"),
    ("DEMO-ACT-003", "Follow up penawaran Fuel Gas Heater Package", "Follow Up", -1, 3, "DEMO-CUS-001", "Andi Wijaya", "Open"),
    ("DEMO-ACT-004", "WhatsApp follow-up proposal", "WhatsApp", -2, 2, "DEMO-CUS-002", "Sari Lestari", "Open"),
    ("DEMO-ACT-005", "Customer meeting - Power Control Upgrade", "Meeting", 1, 5, "DEMO-CUS-003", "Dina Pratama", "Open"),
    ("DEMO-ACT-006", "Call overdue quotation confirmation", "Call", -4, -1, "DEMO-CUS-004", "Andi Wijaya", "Open"),
    ("DEMO-ACT-007", "Email overdue technical clarification", "Email", -6, -2, "DEMO-CUS-005", "Sari Lestari", "Open"),
    ("DEMO-ACT-008", "Presentation - Remote I/O solution", "Presentation", -3, None, "DEMO-CUS-005", "Dina Pratama", "Completed"),
    ("DEMO-ACT-009", "Visit completed - Petrochemical project", "Visit", -8, None, "DEMO-CUS-004", "Andi Wijaya", "Completed"),
    ("DEMO-ACT-010", "Other - Internal opportunity review", "Other", -10, None, "DEMO-CUS-003", "Sari Lestari", "Cancelled"),
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


    # Quotations: add ten stable demo records covering all quotation
    # statuses. Numbers are generated with the same server sequence used by
    # real quotations, while stable demo IDs keep the seed idempotent.
    for index, (quotation_id, customer_id, customer_name, sales_name, description, status, total_value, quantity, unit_price) in enumerate(DEMO_QUOTATIONS):
        if await db.quotations.find_one({"id": quotation_id}):
            continue

        customer_ref = customer_ids.get(customer_id)
        items = [{
            "product_id": None,
            "description": description,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount": 0,
            "tax": 11,
            "total": quantity * unit_price,
        }]
        subtotal = quantity * unit_price
        tax = subtotal * 0.11
        doc = {
            "id": quotation_id,
            "number": await next_number("quotations", "QT"),
            "customer_id": customer_ref or customer_id,
            "customer_name": customer_name,
            "sales_name": sales_name,
            "date": (date.today() - timedelta(days=index + 1)).isoformat(),
            "valid_until": (date.today() + timedelta(days=14 - index)).isoformat(),
            "payment_term": "30 days",
            "delivery_term": "Ex-warehouse",
            "notes": "Demo quotation for CRM Quotations UI verification.",
            "items": items,
            "subtotal": subtotal,
            "discount_total": 0,
            "tax_total": tax,
            "grand_total": total_value + tax,
            "status": status,
            "is_demo": True,
            "demo_label": "CRM UI demo data",
            "created_at": now() - timedelta(days=index + 1),
            "updated_at": now(),
        }
        await db.quotations.insert_one(doc)

    # Activities: add ten stable demo records covering today, upcoming,
    # overdue, completed, and cancelled states. Sales are resolved from
    # the same Users collection used by Customers and Sales Pipeline.
    for activity_id, subject, activity_type, date_offset, followup_offset, customer_id, sales_name, status in DEMO_ACTIVITIES:
        if await db.activities.find_one({"activity_id": activity_id}):
            continue

        sales = await db.users.find_one({"name": sales_name})
        customer_ref = customer_ids.get(customer_id)

        doc = {
            "id": new_id(),
            "activity_id": activity_id,
            "subject": subject,
            "activity_type": activity_type,
            "date": (date.today() + timedelta(days=date_offset)).isoformat(),
            "customer_id": customer_ref or customer_id,
            "customer_name": next(
                (
                    customer[1]
                    for customer in DEMO_CUSTOMERS
                    if customer[0] == customer_id
                ),
                "",
            ),
            "sales_id": sales["id"] if sales else None,
            "sales_name": sales_name,
            "next_follow_up": (
                (date.today() + timedelta(days=followup_offset)).isoformat()
                if followup_offset is not None
                else None
            ),
            "status": status,
            "description": "Demo activity for CRM Aktivitas Sales UI verification.",
            "is_demo": True,
            "demo_label": "CRM UI demo data",
            "created_at": now(),
        }
        await db.activities.insert_one(doc)

    print("CRM demo data ready: 5 customers, 5 pipeline opportunities, 10 activities, 10 quotations, 3 users")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_demo_data())
