"""Idempotent demo dataset for end-to-end CRM module verification.

This seed is intentionally limited to records marked ``is_demo=True``.
It never deletes or updates normal production records. Demo records use
stable IDs so repeated application starts are safe.
"""
from datetime import date, timedelta

from lib.db import db
from routers.common import new_id, now, next_number


CUSTOMERS = [
    ("DEMO-CUS-001", "PT Nusantara Petro Energy", "Oil & Gas", "Balikpapan", "Rizky Hidayat", "Procurement Manager"),
    ("DEMO-CUS-002", "PT Garuda Industrial Systems", "Manufacturing", "Jakarta", "Maya Putri", "Engineering Manager"),
    ("DEMO-CUS-003", "PT Prima Power Generation", "Power Generation", "Cilegon", "Bambang Setiawan", "Project Manager"),
    ("DEMO-CUS-004", "PT Samudra Petrochemical", "Petrochemical", "Cilacap", "Dewi Anggraini", "Maintenance Manager"),
    ("DEMO-CUS-005", "PT Mitra Automation Integrasi", "System Integrator", "Jakarta", "Fajar Nugroho", "Director"),
]

OPPORTUNITIES = [
    ("DEMO-OPP-001", "Fuel Gas Heater Package", 850_000_000, 60, "Proposal", "Watlow", "Electric Heater"),
    ("DEMO-OPP-002", "Industrial PC Modernization", 425_000_000, 40, "Qualification", "Axiomtek", "Industrial PC"),
    ("DEMO-OPP-003", "Power Control Upgrade", 675_000_000, 70, "Negotiation", "Eurotherm", "Epack"),
    ("DEMO-OPP-004", "Process Temperature Monitoring", 310_000_000, 20, "Lead", "Watlow", "Temperature Controller"),
    ("DEMO-OPP-005", "Remote I/O & Industrial Network", 195_000_000, 100, "Won", "ICP DAS", "Remote I/O"),
]

QUOTATIONS = [
    ("DEMO-QT-001", "DEMO-CUS-001", "Fuel Gas Heater Package - Budgetary", "Draft", 850_000_000, 1, 850_000_000),
    ("DEMO-QT-002", "DEMO-CUS-002", "Industrial PC Modernization Proposal", "Sent", 425_000_000, 1, 425_000_000),
    ("DEMO-QT-003", "DEMO-CUS-003", "Power Control Upgrade", "Negotiation", 675_000_000, 1, 675_000_000),
    ("DEMO-QT-004", "DEMO-CUS-004", "Process Temperature Monitoring", "Approved", 310_000_000, 2, 155_000_000),
    ("DEMO-QT-005", "DEMO-CUS-005", "Remote I/O & Industrial Network", "Converted", 195_000_000, 1, 195_000_000),
    ("DEMO-QT-006", "DEMO-CUS-001", "Electric Heater Replacement", "Rejected", 275_000_000, 1, 275_000_000),
    ("DEMO-QT-007", "DEMO-CUS-002", "Industrial Network Expansion", "Expired", 185_000_000, 5, 37_000_000),
    ("DEMO-QT-008", "DEMO-CUS-003", "Epack Power Controller", "Draft", 240_000_000, 2, 120_000_000),
    ("DEMO-QT-009", "DEMO-CUS-004", "Temperature Controller Upgrade", "Sent", 165_000_000, 3, 55_000_000),
    ("DEMO-QT-010", "DEMO-CUS-005", "Remote I/O Solution Package", "Negotiation", 360_000_000, 4, 90_000_000),
]

PURCHASE_ORDERS = [
    ("DEMO-PO-001", "PO/CUST/DEMO/0001", "DEMO-CUS-001", "Fuel Gas Heater Package", 1, 850_000_000, "Received", "Watlow", "2026-09-25"),
    ("DEMO-PO-002", "PO/CUST/DEMO/0002", "DEMO-CUS-002", "Industrial PC Modernization", 2, 212_500_000, "Processing", "Axiomtek", "2026-10-05"),
    ("DEMO-PO-003", "PO/CUST/DEMO/0003", "DEMO-CUS-003", "Epack Power Controller", 3, 120_000_000, "Ready Stock", "Eurotherm", "2026-09-20"),
    ("DEMO-PO-004", "PO/CUST/DEMO/0004", "DEMO-CUS-004", "Temperature Controller Upgrade", 4, 55_000_000, "Delivery", "Watlow", "2026-10-12"),
    ("DEMO-PO-005", "PO/CUST/DEMO/0005", "DEMO-CUS-005", "Remote I/O Solution Package", 5, 90_000_000, "Completed", "ICP DAS", "2026-09-18"),
]

ACTIVITIES = [
    ("DEMO-ACT-001", "Customer Visit - PT Nusantara Petro Energy", "Call", 0, 5, "DEMO-CUS-001", "Open"),
    ("DEMO-ACT-002", "Technical Discussion - Industrial PC Requirement", "Meeting", 0, 7, "DEMO-CUS-002", "Open"),
    ("DEMO-ACT-003", "Follow up penawaran Fuel Gas Heater Package", "Follow Up", -1, 3, "DEMO-CUS-001", "Open"),
    ("DEMO-ACT-004", "WhatsApp follow-up proposal", "WhatsApp", -2, 2, "DEMO-CUS-002", "Open"),
    ("DEMO-ACT-005", "Customer meeting - Power Control Upgrade", "Meeting", 1, 5, "DEMO-CUS-003", "Open"),
    ("DEMO-ACT-006", "Call overdue quotation confirmation", "Call", -4, -1, "DEMO-CUS-004", "Open"),
    ("DEMO-ACT-007", "Email overdue technical clarification", "Email", -6, -2, "DEMO-CUS-005", "Open"),
    ("DEMO-ACT-008", "Presentation - Remote I/O solution", "Presentation", -3, None, "DEMO-CUS-005", "Completed"),
    ("DEMO-ACT-009", "Visit completed - Petrochemical project", "Visit", -8, None, "DEMO-CUS-004", "Completed"),
    ("DEMO-ACT-010", "Other - Internal opportunity review", "Other", -10, None, "DEMO-CUS-003", "Cancelled"),
]


async def _sales_users() -> list[dict]:
    docs = await db.users.find(
        {"role": "SALES", "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]}},
        {"_id": 0, "id": 1, "name": 1},
    ).sort("name", 1).to_list(100)
    return docs


async def seed_demo_data():
    sales = await _sales_users()
    if not sales:
        print("CRM demo seed skipped: no active SALES user found")
        return

    customer_ids: dict[str, str] = {}
    for index, (customer_id, name, industry, city, pic, position) in enumerate(CUSTOMERS):
        existing = await db.customers.find_one({"customer_id": customer_id}, {"_id": 0, "id": 1})
        if existing:
            customer_ids[customer_id] = str(existing["id"])
            continue
        owner = sales[index % len(sales)]
        doc = {
            "id": new_id(), "customer_id": customer_id, "name": name,
            "company_name": name, "company": name, "industry": industry,
            "city": city, "province": "DKI Jakarta" if city == "Jakarta" else "",
            "phone": "+62 21 7000 1000", "email": f"{customer_id.lower()}@demo.co.id",
            "pic_name": pic, "pic_position": position, "source": "Demo / UI Testing",
            "status": "Active", "sales_id": owner["id"], "sales_name": owner["name"],
            "address": f"Kawasan Industri {city}", "notes": "Demo record for CRM module verification.",
            "is_demo": True, "demo_label": "CRM UI demo data",
            "created_at": now() - timedelta(days=index + 1), "updated_at": now(),
        }
        await db.customers.insert_one(doc)
        customer_ids[customer_id] = doc["id"]

    for index, (opp_id, name, value, probability, stage, brand, product) in enumerate(OPPORTUNITIES):
        if await db.opportunities.find_one({"opportunity_id": opp_id}):
            continue
        customer_id, customer_name, *_ = CUSTOMERS[index]
        owner = sales[index % len(sales)]
        await db.opportunities.insert_one({
            "id": new_id(), "opportunity_id": opp_id, "name": name,
            "customer_id": customer_ids[customer_id], "customer_name": customer_name,
            "sales_id": owner["id"], "sales_name": owner["name"], "value": value,
            "probability": probability, "stage": stage,
            "target_close": (date.today() + timedelta(days=15 + index * 12)).isoformat(),
            "brand": brand, "product": product,
            "next_action": "Follow up customer requirement and commercial proposal",
            "description": "Demo opportunity for Sales Pipeline UI verification.",
            "is_demo": True, "demo_label": "CRM UI demo data",
            "created_at": now() - timedelta(days=index + 2), "updated_at": now(),
        })

    for index, (qid, customer_id, description, status, total_value, quantity, unit_price) in enumerate(QUOTATIONS):
        if await db.quotations.find_one({"id": qid}):
            continue
        customer = next(item for item in CUSTOMERS if item[0] == customer_id)
        owner = sales[index % len(sales)]
        subtotal = quantity * unit_price
        tax = subtotal * 0.11
        await db.quotations.insert_one({
            "id": qid, "number": await next_number("quotations", "QT"),
            "customer_id": customer_ids[customer_id], "customer_name": customer[1],
            "sales_name": owner["name"], "sales_id": owner["id"],
            "date": (date.today() - timedelta(days=index + 1)).isoformat(),
            "valid_until": (date.today() + timedelta(days=14 - index)).isoformat(),
            "payment_term": "30 days", "delivery_term": "Ex-warehouse",
            "notes": "Demo quotation for CRM verification.",
            "items": [{"product_id": None, "description": description, "quantity": quantity,
                       "unit_price": unit_price, "discount": 0, "tax": 11,
                       "total": subtotal}],
            "subtotal": subtotal, "discount_total": 0, "tax_total": tax,
            "grand_total": total_value + tax, "status": status,
            "is_demo": True, "demo_label": "CRM UI demo data",
            "created_at": now() - timedelta(days=index + 1), "updated_at": now(),
        })

    quotation_numbers = {}
    for qid, customer_id, *_ in QUOTATIONS:
        q = await db.quotations.find_one({"id": qid}, {"_id": 0, "number": 1})
        if q and q.get("number") and customer_id not in quotation_numbers:
            quotation_numbers[customer_id] = q["number"]

    for index, (poid, po_number, customer_id, description, quantity, unit_price, status, supplier, eta) in enumerate(PURCHASE_ORDERS):
        if await db.purchase_orders.find_one({"id": poid}):
            continue
        customer = next(item for item in CUSTOMERS if item[0] == customer_id)
        owner = sales[index % len(sales)]
        await db.purchase_orders.insert_one({
            "id": poid, "po_number": po_number, "date": date.today().isoformat(),
            "customer_id": customer_ids[customer_id], "customer_name": customer[1],
            "quotation_number": quotation_numbers.get(customer_id),
            "sales_id": owner["id"], "sales_name": owner["name"],
            "items": [{"product_id": None, "description": description, "quantity": quantity, "unit_price": unit_price}],
            "total": quantity * unit_price, "status": status, "eta": eta, "supplier": supplier,
            "shipping_address": customer[1], "document_name": None,
            "is_demo": True, "demo_label": "CRM UI demo data", "created_at": now(), "updated_at": now(),
        })

    for index, (aid, subject, activity_type, date_offset, followup_offset, customer_id, status) in enumerate(ACTIVITIES):
        if await db.activities.find_one({"activity_id": aid}):
            continue
        customer = next(item for item in CUSTOMERS if item[0] == customer_id)
        owner = sales[index % len(sales)]
        await db.activities.insert_one({
            "id": new_id(), "activity_id": aid, "subject": subject, "activity_type": activity_type,
            "date": (date.today() + timedelta(days=date_offset)).isoformat(),
            "customer_id": customer_ids[customer_id], "customer_name": customer[1],
            "sales_id": owner["id"], "sales_name": owner["name"],
            "next_follow_up": (date.today() + timedelta(days=followup_offset)).isoformat() if followup_offset is not None else None,
            "status": status, "description": "Demo activity for CRM verification.",
            "is_demo": True, "demo_label": "CRM UI demo data", "created_at": now(), "updated_at": now(),
        })

    if await db.contacts.count_documents({}) == 0:
        for index, customer in enumerate(CUSTOMERS):
            owner = sales[index % len(sales)]
            await db.contacts.insert_one({
                "id": new_id(), "contact_id": f"DEMO-CON-{index + 1:03d}",
                "customer_id": customer_ids[customer[0]], "customer_name": customer[1],
                "first_name": customer[4].split()[0], "last_name": " ".join(customer[4].split()[1:]),
                "position": customer[5], "department": "Procurement", "email": f"contact{index+1}@demo.co.id",
                "mobile": f"+62 812 9000 {index+1:04d}", "contact_type": "Procurement",
                "is_decision_maker": index % 2 == 0, "status": "Active",
                "sales_id": owner["id"], "sales_name": owner["name"],
                "is_demo": True, "demo_label": "CRM UI demo data", "created_at": now(),
            })

    if await db.leads.count_documents({}) == 0:
        for index, customer in enumerate(CUSTOMERS):
            owner = sales[index % len(sales)]
            await db.leads.insert_one({
                "id": new_id(), "lead_number": f"LEAD-DEMO-{index+1:03d}",
                "lead_date": (date.today() - timedelta(days=index * 2)).isoformat(),
                "company": customer[1], "customer_id": customer_ids[customer[0]],
                "source": "Website" if index % 2 == 0 else "Referral", "industry": customer[2],
                "product_interest": "Industrial Automation", "estimated_value": 150_000_000 + index * 25_000_000,
                "currency": "IDR", "probability": 25 + index * 10, "status": ["New", "Contacted", "Qualified"][index % 3],
                "sales_id": owner["id"], "sales_name": owner["name"],
                "is_demo": True, "demo_label": "CRM UI demo data", "created_at": now(),
            })

    if await db.sales_targets.count_documents({"is_demo": True}) == 0:
        owner = sales[0]
        await db.sales_targets.insert_many([
            {"id": new_id(), "year": date.today().year, "month": month,
             "sales_id": owner["id"], "sales_name": owner["name"], "team": "Industrial Sales",
             "target": 750_000_000, "currency": "IDR", "is_demo": True,
             "demo_label": "CRM UI demo data", "created_at": now()}
            for month in range(1, 13)
        ])

    print("CRM demo dataset ready: customers + contacts + leads + pipeline + activities + quotations + purchase orders + targets")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_demo_data())
