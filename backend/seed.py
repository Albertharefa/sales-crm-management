import asyncio
from datetime import date, timedelta
from passlib.context import CryptContext
from lib.db import db, client
from routers.common import new_id, now

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
industries = ["Oil & Gas", "Power Generation", "Electricity", "Petrochemical", "Manufacturing", "Mining", "Cement", "Water Treatment", "EPC", "System Integrator"]
cities = ["Jakarta", "Balikpapan", "Cilacap", "Dumai", "Plaju", "Cilegon", "Surabaya", "Bandung", "Bekasi"]
stages = ["Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"]
categories = ["Computing", "Automation", "Motion", "Drives", "Sensor", "Safety", "Networking", "Vision", "Pneumatic", "Power"]


async def seed():
    if await db.users.count_documents({}) == 0:
        users = [
            {"id": "admin-0001", "user_id": "USR-0001", "name": "Admin", "email": "admin@crm.co.id", "role": "SUPER_ADMIN", "phone": "+62 811 0000 0001", "status": "Active", "password_hash": pwd.hash("Password123"), "created_at": now()},
            {"id": "manager-0001", "user_id": "USR-0002", "name": "Rina Manager", "email": "manager@crm.co.id", "role": "SALES_MANAGER", "phone": "+62 811 0000 0002", "status": "Active", "password_hash": pwd.hash("Password123"), "created_at": now()},
            {"id": "sales-0001", "user_id": "USR-0003", "name": "Budi Santoso", "email": "sales@crm.co.id", "role": "SALES", "manager_id": "manager-0001", "phone": "+62 811 0000 0003", "status": "Active", "password_hash": pwd.hash("Password123"), "created_at": now()},
        ]
        await db.users.insert_many(users)
    if await db.customers.count_documents({}) == 0:
        customers = []
        for i in range(50):
            customers.append({"id": new_id(), "customer_id": f"CUS-2026-{i+1:05d}", "name": f"PT Industri {i+1:02d}", "industry": industries[i % len(industries)], "city": cities[i % len(cities)], "province": "DKI Jakarta", "phone": f"+62 21 555 {i:04d}", "email": f"procurement{i+1:02d}@industri.co.id", "pic_name": f"PIC {i+1:02d}", "pic_position": "Procurement Manager", "source": "Referral" if i % 2 else "Website", "status": "Active" if i % 5 else "Prospect", "sales_id": "sales-0001", "sales_name": "Budi Santoso", "address": f"Kawasan Industri Blok {i+1}", "created_at": now() - timedelta(days=i), "updated_at": now()})
        await db.customers.insert_many(customers)
    customers = await db.customers.find({}).to_list(100)
    if await db.products.count_documents({}) == 0:
        products = [{"id": new_id(), "code": f"PRD-{i+1:04d}", "name": f"Industrial Product {i+1:02d}", "brand": f"Brand {i%15+1:02d}", "category": categories[i % len(categories)], "unit": "pcs", "default_price": 1250000 + i * 850000, "supplier": f"Principal {i%15+1:02d}", "status": "Active", "description": "Industrial automation and engineering product", "created_at": now()} for i in range(50)]
        await db.products.insert_many(products)
    products = await db.products.find({}).to_list(100)
    if await db.opportunities.count_documents({}) == 0:
        opps = []
        for i in range(50):
            c = customers[i % len(customers)]
            opps.append({"id": new_id(), "opportunity_id": f"OPP-2026-{i+1:05d}", "name": f"Project Expansion {i+1:02d}", "customer_id": c["id"], "customer_name": c["name"], "sales_id": "sales-0001", "sales_name": "Budi Santoso", "value": 85000000 + i * 17500000, "probability": [20, 40, 60, 70, 100, 0][i % 6], "stage": stages[i % 6], "target_close": (date.today() + timedelta(days=i * 3)).isoformat(), "brand": f"Brand {i%15+1:02d}", "product": products[i % len(products)]["name"], "next_action": "Follow-up technical requirement", "created_at": now() - timedelta(days=i)})
        await db.opportunities.insert_many(opps)
    if await db.quotations.count_documents({}) == 0:
        quotes = []
        for i in range(30):
            c = customers[i % len(customers)]; p = products[i % len(products)]; total = p["default_price"] * (i % 4 + 1)
            quotes.append({"id": new_id(), "number": f"QT-2026-{i+1:05d}", "date": (date.today() - timedelta(days=i)).isoformat(), "customer_id": c["id"], "customer_name": c["name"], "sales_name": "Budi Santoso", "items": [{"product_id": p["id"], "description": p["name"], "quantity": i%4+1, "unit_price": p["default_price"], "discount": 0, "tax": 11}], "subtotal": total, "discount_total": 0, "tax_total": total*.11, "grand_total": total*1.11, "status": ["Draft", "Sent", "Approved", "Negotiation"][i%4], "created_at": now() - timedelta(days=i)})
        await db.quotations.insert_many(quotes)
        await db.number_sequences.update_one({"key": "QT-2026"}, {"$set": {"value": 30}}, upsert=True)
    if await db.purchase_orders.count_documents({}) == 0:
        orders = []
        for i in range(20):
            c = customers[i % len(customers)]; p = products[i % len(products)]; qty = i % 4 + 1; total = p["default_price"] * qty
            orders.append({"id": new_id(), "po_number": f"PO/CUST/2026/{i+1:04d}", "date": (date.today() - timedelta(days=i)).isoformat(), "customer_id": c["id"], "customer_name": c["name"], "quotation_number": f"QT-2026-{i+1:05d}", "sales_name": "Budi Santoso", "items": [{"product_id": p["id"], "description": p["name"], "quantity": qty, "unit_price": p["default_price"]}], "total": total, "status": ["Received", "Processing", "Indent", "Ready Stock", "Delivery", "Completed"][i%6], "eta": (date.today() + timedelta(days=i-5)).isoformat(), "supplier": p["supplier"], "created_at": now() - timedelta(days=i)})
        await db.purchase_orders.insert_many(orders)
    if await db.activities.count_documents({}) == 0:
        activities = []
        for i in range(100):
            c = customers[i % len(customers)]
            activities.append({"id": new_id(), "activity_id": f"ACT-{i+1:05d}", "subject": ["Customer Visit", "Technical Discussion", "Follow-up Quotation", "Online Meeting"][i%4], "activity_type": ["Visit", "Meeting", "Follow Up", "Email"][i%4], "date": (date.today() - timedelta(days=i%30)).isoformat(), "customer_id": c["id"], "customer_name": c["name"], "sales_id": "sales-0001", "sales_name": "Budi Santoso", "next_follow_up": (date.today() + timedelta(days=i%10)).isoformat(), "status": "Completed" if i%3 == 0 else "Open", "description": "Requirement discovery and commercial follow-up", "created_at": now() - timedelta(days=i)})
        await db.activities.insert_many(activities)
    if await db.tasks.count_documents({}) == 0:
        await db.tasks.insert_many([{"id": new_id(), "title": f"Follow-up task {i+1:02d}", "due_date": (date.today() + timedelta(days=i-5)).isoformat(), "priority": ["Low", "Medium", "High", "Urgent"][i%4], "status": "Completed" if i%5 == 0 else "Pending", "customer_name": customers[i%len(customers)]["name"], "opportunity_name": f"Project Expansion {i+1:02d}", "assigned_user": "Budi Santoso", "created_at": now()} for i in range(50)])
    for collection in ["contacts", "leads", "projects", "tenders", "audit_logs", "sessions", "documents", "number_sequences"]:
        await db[collection].create_index("created_at")
    for collection, fields in {"users":["email","role"], "customers":["customer_id","name","status"], "products":["code","category"], "opportunities":["opportunity_id","stage"], "purchase_orders":["po_number","status"]}.items():
        for field in fields:
            await db[collection].create_index(field)
    print("CRM seed ready")


if __name__ == "__main__":
    asyncio.run(seed())
    client.close()