"""Non-destructive CRM demo dataset for end-to-end UI verification.

The seed never deletes or modifies production records. It normalizes the demo
customers to the classic 15-row dataset and fills every operational module
with deterministic demo scenarios when records are missing.
"""
from datetime import timedelta

from lib.db import db
from routers.common import new_id, now

CUSTOMER_COUNT = 15
INDUSTRIES = ["Manufacturing", "Oil & Gas", "Automation", "Food & Beverage", "Power Generation"]
CITIES = ["Jakarta", "Bekasi", "Cilegon", "Balikpapan", "Surabaya"]
POSITIONS = ["Procurement", "Engineering", "Maintenance", "Project", "Director"]
ACTIVITY_TYPES = ["Call", "WhatsApp", "Email", "Meeting", "Visit", "Presentation", "Follow Up", "Other"]
OPPORTUNITY_STAGES = ["Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"]
QUOTATION_STATUSES = ["Draft", "Sent", "Negotiation", "Approved", "Rejected", "Expired", "Converted"]
ORDER_STAGES = ["Received", "Waiting Order", "Processing", "Indent", "Ready Stock", "Delivery", "Completed", "Cancelled"]


async def _sales_users() -> list[dict]:
    return await db.users.find(
        {"role": "SALES", "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]}},
        {"_id": 0, "id": 1, "name": 1},
    ).sort("name", 1).to_list(100)


async def _normalize_customers(sales: list[dict]) -> dict[str, str]:
    demo = await db.customers.find({"is_demo": True}, {"_id": 0}).to_list(1000)
    by_customer_id = {str(x.get("customer_id")): x for x in demo if x.get("customer_id")}
    legacy = [x for x in demo if str(x.get("customer_id", "")).startswith("DEMO-CUS-")]
    legacy.sort(key=lambda x: str(x.get("customer_id")))
    result: dict[str, str] = {}

    for index in range(1, CUSTOMER_COUNT + 1):
        customer_id = f"CUS-DEMO-{index:03d}"
        name = f"Demo Customer {index:02d}"
        owner = sales[(index - 1) % len(sales)]
        doc = by_customer_id.get(customer_id)
        if doc is None and index >= 11 and legacy:
            doc = legacy.pop(0)

        fields = {
            "customer_id": customer_id,
            "name": name,
            "company_name": f"PT Demo Industri {index:02d}",
            "company": f"PT Demo Industri {index:02d}",
            "industry": INDUSTRIES[(index - 1) % len(INDUSTRIES)],
            "city": CITIES[(index - 1) % len(CITIES)],
            "province": "DKI Jakarta" if CITIES[(index - 1) % len(CITIES)] == "Jakarta" else "",
            "phone": f"021555{index:04d}",
            "email": f"customer{index:02d}@crm-demo.local",
            "pic_name": f"PIC Demo {index:02d}",
            "pic_position": POSITIONS[(index - 1) % len(POSITIONS)],
            "source": "Dummy Data",
            "status": "Active",
            "sales_id": owner["id"],
            "sales_name": owner["name"],
            "address": f"Jl. Demo Industri No. {index}, {CITIES[(index - 1) % len(CITIES)]}",
            "notes": "Demo record for complete CRM module verification.",
            "is_demo": True,
            "demo_label": "CRM UI demo data",
            "updated_at": now(),
        }
        if doc is None:
            fields["id"] = new_id()
            fields["created_at"] = now() - timedelta(days=index)
            await db.customers.insert_one(fields)
            internal_id = fields["id"]
        else:
            await db.customers.update_one({"id": doc["id"]}, {"$set": fields})
            internal_id = doc["id"]
        result[customer_id] = str(internal_id)
    return result


async def _ensure_products() -> list[dict]:
    docs = await db.products.find({"is_demo": True}, {"_id": 0}).sort("code", 1).to_list(100)
    by_code = {str(x.get("code")): x for x in docs}
    products = []
    brands = ["Axiomtek", "Watlow", "ICPDAS", "Eurotherm"]
    categories = ["Industrial PC", "Heater", "Remote I/O", "Controller"]
    for index in range(1, 11):
        code = f"PRD-DEMO-{index:03d}"
        doc = by_code.get(code)
        if doc is None:
            doc = {
                "id": new_id(), "code": code, "name": f"Demo Product {index:02d}",
                "brand": brands[(index - 1) % 4], "category": categories[(index - 1) % 4],
                "unit": "pcs", "default_price": float(index * 2500000), "supplier": "Demo Supplier",
                "status": "Active", "description": "Demo product for CRM verification.",
                "is_demo": True, "demo_label": "CRM UI demo data", "created_at": now(), "updated_at": now(),
            }
            await db.products.insert_one(doc)
        products.append(doc)
    return products


async def _ensure_opportunities(customer_ids: dict[str, str], sales: list[dict], products: list[dict]) -> list[dict]:
    existing = await db.opportunities.find({"is_demo": True}, {"_id": 0}).to_list(1000)
    by_id = {str(x.get("opportunity_id")): x for x in existing if x.get("opportunity_id")}
    result = []
    for index in range(1, 16):
        oid = f"OPP-DEMO-{index:03d}"
        customer_id = f"CUS-DEMO-{((index - 1) % CUSTOMER_COUNT) + 1:03d}"
        sales_user = sales[(index - 1) % len(sales)]
        stage = OPPORTUNITY_STAGES[(index - 1) % len(OPPORTUNITY_STAGES)]
        customer_name = f"Demo Customer {((index - 1) % CUSTOMER_COUNT) + 1:02d}"
        doc = by_id.get(oid)
        if doc is None:
            doc = {
                "id": new_id(), "opportunity_id": oid, "name": f"Demo Opportunity {index:02d}",
                "customer_id": customer_ids[customer_id], "customer_name": customer_name,
                "sales_id": sales_user["id"], "sales_name": sales_user["name"],
                "value": float(50000000 + index * 17500000),
                "probability": {"Lead": 10, "Qualification": 25, "Proposal": 50, "Negotiation": 75, "Won": 100, "Lost": 0}[stage],
                "stage": stage, "target_close": (now() + timedelta(days=15 + index)).date().isoformat(),
                "brand": products[(index - 1) % len(products)]["brand"],
                "product": products[(index - 1) % len(products)]["name"],
                "next_action": "Follow up customer", "description": "Demo opportunity for CRM verification.",
                "loss_reason": "Budget / competition" if stage == "Lost" else None,
                "is_demo": True, "demo_label": "CRM UI demo data", "created_at": now() - timedelta(days=index), "updated_at": now(),
            }
            await db.opportunities.insert_one(doc)
        result.append(doc)
    return result


async def _ensure_activities(customer_ids: dict[str, str], opportunities: list[dict], sales: list[dict]) -> None:
    existing = await db.activities.find({"is_demo": True}, {"_id": 0}).to_list(1000)
    existing_ids = {str(x.get("activity_id")) for x in existing if x.get("activity_id")}
    for index in range(1, 16):
        aid = f"ACT-DEMO-{index:03d}"
        if aid in existing_ids:
            continue
        customer_no = ((index - 1) % CUSTOMER_COUNT) + 1
        customer_key = f"CUS-DEMO-{customer_no:03d}"
        sales_user = sales[(index - 1) % len(sales)]
        if index in {1, 6, 11}:
            activity_date = now().date().isoformat()
            follow_up = (now() + timedelta(days=3)).date().isoformat()
        elif index in {2, 7, 12}:
            activity_date = (now() - timedelta(days=2)).date().isoformat()
            follow_up = (now() - timedelta(days=1)).date().isoformat()
        elif index in {3, 8, 13}:
            activity_date = (now() - timedelta(days=1)).date().isoformat()
            follow_up = (now() + timedelta(days=7)).date().isoformat()
        else:
            activity_date = (now() - timedelta(days=index)).date().isoformat()
            follow_up = (now() + timedelta(days=index)).date().isoformat()
        status = "Completed" if index in {4, 8, 12, 15} else "Open"
        opportunity = opportunities[(index - 1) % len(opportunities)]
        await db.activities.insert_one({
            "id": new_id(), "activity_id": aid, "subject": f"Demo Activity {index:02d}",
            "activity_type": ACTIVITY_TYPES[(index - 1) % len(ACTIVITY_TYPES)], "date": activity_date,
            "customer_id": customer_ids[customer_key], "customer_name": f"Demo Customer {customer_no:02d}",
            "opportunity_id": opportunity["id"], "sales_id": sales_user["id"], "sales_name": sales_user["name"],
            "next_follow_up": follow_up, "status": status, "description": "Demo activity for CRM verification.",
            "is_demo": True, "demo_label": "CRM UI demo data", "created_at": now(), "updated_at": now(),
        })


async def _ensure_quotations(customer_ids: dict[str, str], opportunities: list[dict], sales: list[dict], products: list[dict]) -> None:
    existing = await db.quotations.find({"is_demo": True}, {"_id": 0}).to_list(1000)
    existing_ids = {str(x.get("number")) for x in existing if x.get("number")}
    for index in range(1, 21):
        number = f"QT-DEMO-{index:03d}"
        if number in existing_ids:
            continue
        customer_no = ((index - 1) % CUSTOMER_COUNT) + 1
        customer_key = f"CUS-DEMO-{customer_no:03d}"
        sales_user = sales[(index - 1) % len(sales)]
        product = products[(index - 1) % len(products)]
        opportunity = opportunities[(index - 1) % len(opportunities)]
        qty = (index % 3) + 1
        subtotal = float(product["default_price"]) * qty
        discount_total = subtotal * (0.05 if index % 4 == 0 else 0)
        tax_total = (subtotal - discount_total) * 0.11
        await db.quotations.insert_one({
            "id": new_id(), "number": number, "customer_id": customer_ids[customer_key],
            "customer_name": f"Demo Customer {customer_no:02d}", "sales_id": sales_user["id"], "sales_name": sales_user["name"],
            "opportunity_id": opportunity["id"], "date": (now() - timedelta(days=index)).date().isoformat(),
            "valid_until": (now() + timedelta(days=30)).date().isoformat(), "payment_term": "30 Days", "delivery_term": "4-6 Weeks",
            "notes": "Demo quotation for CRM verification.",
            "items": [{"product_id": product["id"], "description": product["name"], "quantity": qty, "unit_price": float(product["default_price"]),
                       "discount": discount_total, "tax": tax_total, "total": subtotal - discount_total + tax_total}],
            "subtotal": subtotal, "discount_total": discount_total, "tax_total": tax_total,
            "grand_total": subtotal - discount_total + tax_total,
            "status": QUOTATION_STATUSES[(index - 1) % len(QUOTATION_STATUSES)],
            "is_demo": True, "demo_label": "CRM UI demo data", "created_at": now(), "updated_at": now(),
        })


async def _ensure_purchase_orders(customer_ids: dict[str, str], sales: list[dict], products: list[dict]) -> None:
    existing = await db.purchase_orders.find({"is_demo": True}, {"_id": 0}).to_list(1000)
    existing_ids = {str(x.get("po_number")) for x in existing if x.get("po_number")}
    for index in range(1, 11):
        po_number = f"PO-DEMO-{index:03d}"
        if po_number in existing_ids:
            continue
        customer_no = ((index - 1) % CUSTOMER_COUNT) + 1
        customer_key = f"CUS-DEMO-{customer_no:03d}"
        sales_user = sales[(index - 1) % len(sales)]
        product = products[(index - 1) % len(products)]
        qty = (index % 3) + 1
        await db.purchase_orders.insert_one({
            "id": new_id(), "po_number": po_number, "customer_id": customer_ids[customer_key],
            "customer_name": f"Demo Customer {customer_no:02d}", "sales_id": sales_user["id"], "sales_name": sales_user["name"],
            "date": (now() - timedelta(days=index)).date().isoformat(), "status": ORDER_STAGES[(index - 1) % len(ORDER_STAGES)],
            "quotation_number": f"QT-DEMO-{index:03d}", "quotation_manual": False,
            "items": [{"product_id": product["id"], "description": product["name"], "quantity": qty, "unit_price": float(product["default_price"]), "discount": 0, "tax": 11}],
            "total": float(product["default_price"]) * qty * 1.11,
            "eta": (now() + timedelta(days=index - 4)).date().isoformat(), "payment_term": "30 Days",
            "supplier": "Demo Supplier", "shipping_address": f"Jl. Demo Industri No. {customer_no}",
            "document_name": f"PO-DEMO-{index:03d}.pdf",
            "is_demo": True, "demo_label": "CRM UI demo data", "created_at": now(), "updated_at": now(),
        })


async def _ensure_tasks() -> None:
    existing = await db.tasks.find({"is_demo": True}, {"_id": 0, "title": 1}).to_list(1000)
    existing_titles = {str(x.get("title")) for x in existing}
    for index in range(1, 11):
        title = f"Demo Task {index:02d}"
        if title in existing_titles:
            continue
        await db.tasks.insert_one({
            "id": new_id(), "title": title,
            "due_date": (now() + timedelta(days=index - 5)).date().isoformat(),
            "priority": ["Low", "Medium", "High"][index % 3],
            "status": "Completed" if index in {2, 6, 10} else ("In Progress" if index in {4, 8} else "Pending"),
            "customer_name": f"Demo Customer {index:02d}",
            "opportunity_name": f"Demo Opportunity {index:02d}",
            "assigned_user": "",
            "is_demo": True, "demo_label": "CRM UI demo data", "created_at": now(), "updated_at": now(),
        })


async def _ensure_contacts(customer_ids: dict[str, str]) -> None:
    existing = await db.contacts.find({"is_demo": True}, {"_id": 0, "contact_id": 1}).to_list(1000)
    existing_ids = {str(x.get("contact_id")) for x in existing if x.get("contact_id")}
    for index in range(1, 16):
        contact_id = f"CON-DEMO-{index:03d}"
        if contact_id in existing_ids:
            continue
        customer_no = index
        await db.contacts.insert_one({
            "id": new_id(), "contact_id": contact_id,
            "customer_id": customer_ids[f"CUS-DEMO-{customer_no:03d}"], "customer_name": f"Demo Customer {customer_no:02d}",
            "first_name": f"PIC Demo {customer_no:02d}", "last_name": "Contact",
            "position": POSITIONS[(index - 1) % len(POSITIONS)], "department": "Procurement",
            "mobile": f"08120000{index:04d}", "email": f"pic{index:02d}@crm-demo.local",
            "is_demo": True, "demo_label": "CRM UI demo data", "created_at": now(), "updated_at": now(),
        })


async def _ensure_targets(sales: list[dict]) -> None:
    demo_count = await db.sales_targets.count_documents({"is_demo": True})
    if demo_count >= 12:
        return
    sales_user = sales[0]
    for month in range(1, 13):
        if await db.sales_targets.find_one({"is_demo": True, "sales_id": sales_user["id"], "year": now().year, "month": month}, {"_id": 1}):
            continue
        await db.sales_targets.insert_one({
            "id": new_id(), "sales_id": sales_user["id"], "sales_name": sales_user["name"],
            "year": now().year, "month": month, "target": float(500000000),
            "is_demo": True, "demo_label": "CRM UI demo data", "created_at": now(), "updated_at": now(),
        })


async def _verify_demo_dataset() -> None:
    collections = ["customers", "contacts", "leads", "products", "opportunities", "activities", "quotations", "purchase_orders", "tasks", "sales_targets"]
    counts = {collection: await db[collection].count_documents({"is_demo": True}) for collection in collections}
    stages = await db.opportunities.distinct("stage", {"is_demo": True})
    quotation_statuses = await db.quotations.distinct("status", {"is_demo": True})
    order_statuses = await db.purchase_orders.distinct("status", {"is_demo": True})
    activity_types = await db.activities.distinct("activity_type", {"is_demo": True})
    task_statuses = await db.tasks.distinct("status", {"is_demo": True})
    print("CRM demo verification | counts=%s | pipeline=%s | quotations=%s | orders=%s | activities=%s | tasks=%s", counts, sorted(map(str, stages)), sorted(map(str, quotation_statuses)), sorted(map(str, order_statuses)), sorted(map(str, activity_types)), sorted(map(str, task_statuses)))


async def seed_demo_data():
    sales = await _sales_users()
    if not sales:
        print("CRM demo seed skipped: no active SALES user found")
        return
    customer_ids = await _normalize_customers(sales)
    products = await _ensure_products()
    opportunities = await _ensure_opportunities(customer_ids, sales, products)
    await _ensure_activities(customer_ids, opportunities, sales)
    await _ensure_quotations(customer_ids, opportunities, sales, products)
    await _ensure_purchase_orders(customer_ids, sales, products)
    await _ensure_tasks()
    await _ensure_contacts(customer_ids)
    await _ensure_targets(sales)
    await _verify_demo_dataset()
