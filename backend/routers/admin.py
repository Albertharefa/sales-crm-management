from datetime import datetime, timezone
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from passlib.context import CryptContext
from lib.db import db
from models.crm import Paginated, UserCreate, UserPublic, OptionsResponse, SalesTeamMetric
from routers.common import audit, new_id, now, page_collection
from routers.deps import current_user, require_roles

router = APIRouter(tags=["admin"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def manager_user_ids(user: dict) -> list[str]:
    reports = await db.users.find({"manager_id": user["id"]}, {"id": 1}).to_list(1000)
    return [user["id"], *[item["id"] for item in reports]]


async def visible_sales_ids(user: dict) -> list[str]:
    role = str(user.get("role") or "").strip().upper()
    if role == "SUPER_ADMIN":
        docs = await db.users.find({"role": "SALES", "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]}}, {"id": 1}).to_list(1000)
        return [str(item["id"]) for item in docs if item.get("id")]
    if role == "SALES_MANAGER":
        docs = await db.users.find({"manager_id": user.get("id"), "role": "SALES", "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]}}, {"id": 1}).to_list(1000)
        return [str(item["id"]) for item in docs if item.get("id")]
    if role == "SALES":
        return [str(user.get("id"))]
    return []


@router.get("/users", response_model=Paginated)
async def list_users(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER"))):
    if user.get("role") == "SUPER_ADMIN":
        return await page_collection("users", page, page_size, search)
    visible_ids = await manager_user_ids(user)
    return await page_collection("users", page, page_size, search, {"id": {"$in": visible_ids}})


@router.post("/users", response_model=UserPublic)
async def create_user(payload: UserCreate, user: dict = Depends(require_roles("SUPER_ADMIN"))):
    if await db.users.find_one({"email": payload.email.lower()}):
        raise HTTPException(status_code=409, detail="Email sudah terdaftar")
    count = await db.users.count_documents({}) + 1
    doc = {"id": new_id(), "user_id": f"USR-{count:04d}", "email": payload.email.lower(), "password_hash": pwd_context.hash(payload.password), **payload.model_dump(mode="json", exclude={"password"}), "created_at": now()}
    await db.users.insert_one(doc)
    await audit(user, "Create", "Users", doc["id"], {"email": doc["email"]})
    return UserPublic(**doc)


@router.get("/audit-logs", response_model=Paginated)
async def list_audit_logs(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER"))):
    if user.get("role") == "SUPER_ADMIN":
        return await page_collection("audit_logs", page, page_size, search)
    visible_ids = await manager_user_ids(user)
    visible_users = await db.users.find({"id": {"$in": visible_ids}}, {"name": 1}).to_list(100)
    names = [item["name"] for item in visible_users]
    return await page_collection("audit_logs", page, page_size, search, {"user_name": {"$in": names}})


@router.get("/sales-team", response_model=list[SalesTeamMetric])
async def sales_team(search: str = Query(""), sales_id: str = Query(""), status: str = Query(""), year: int | None = Query(None, ge=2000, le=2100), user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER"))):
    query: dict = {"role": {"$in": ["SALES", "SALES_MANAGER"]}}
    if user.get("role") == "SALES_MANAGER":
        query = {"id": {"$in": await manager_user_ids(user)}, "role": "SALES"}
    if sales_id:
        query["id"] = sales_id
    if search.strip():
        keyword = re.escape(search.strip())
        query["$or"] = [{"name": {"$regex": keyword, "$options": "i"}}, {"id": {"$regex": keyword, "$options": "i"}}, {"user_id": {"$regex": keyword, "$options": "i"}}]
    if status:
        normalized_status = status.strip().lower()
        if normalized_status == "inactive":
            query["status"] = {"$in": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]}
        elif normalized_status == "active":
            query["status"] = {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]}

    users = await db.users.find(query).to_list(100)
    all_users = await db.users.find({}, {"id": 1, "user_id": 1, "name": 1}).to_list(1000)
    user_by_reference = {str(item.get("id")): item for item in all_users if item.get("id")}
    user_by_reference.update({str(item.get("user_id")): item for item in all_users if item.get("user_id")})
    current_year = year or datetime.now(timezone.utc).year
    current_time = datetime.now(timezone.utc)
    result = []

    for person in users:
        sales_id_value = person["id"]
        sales_name = person["name"]
        opportunities = await db.opportunities.find({"$or": [{"sales_id": sales_id_value}, {"sales_name": sales_name}]}).to_list(1000)
        orders = await db.purchase_orders.find({"$or": [{"sales_id": sales_id_value}, {"sales_name": sales_name}]}).to_list(1000)
        activities = await db.activities.find({"$or": [{"sales_id": sales_id_value}, {"sales_name": sales_name}]}).to_list(5000)
        targets = await db.sales_targets.find({"year": current_year, "$or": [{"sales_id": sales_id_value}, {"sales_name": sales_name}]}, {"target": 1}).to_list(1000)
        open_opportunities = [o for o in opportunities if o.get("stage") not in ["Won", "Lost"]]
        won_opportunities = [o for o in opportunities if o.get("stage") == "Won"]
        lost_opportunities = [o for o in opportunities if o.get("stage") == "Lost"]
        target = sum(float(item.get("target", 0) or 0) for item in targets)
        won = sum(float(item.get("value", 0) or 0) for item in won_opportunities)
        gap_to_target = max(0.0, target - won)
        achievement = (won / target * 100) if target else 0.0
        coverage = (sum(float(item.get("value", 0) or 0) for item in open_opportunities) / gap_to_target if gap_to_target > 0 else 0.0)
        closed_count = len(won_opportunities) + len(lost_opportunities)
        win_rate = (len(won_opportunities) / closed_count * 100) if closed_count else 0.0
        overdue_activities = sum(1 for activity in activities if activity.get("status") not in ["Completed", "Cancelled"] and activity.get("next_follow_up") and str(activity.get("next_follow_up"))[:10] < current_time.date().isoformat())
        overdue_orders = sum(1 for order in orders if order.get("status") not in ["Completed", "Cancelled"] and order.get("eta") and str(order.get("eta"))[:10] < current_time.date().isoformat())
        manager_reference = person.get("manager_id")
        manager = user_by_reference.get(str(manager_reference)) if manager_reference else None
        manager_label = f"{manager.get('name')} — {manager.get('user_id')}" if manager and manager.get("name") else "-"
        result.append({"sales": sales_name, "role": person["role"], "manager": manager_label, "target": target, "gap_to_target": gap_to_target, "achievement": achievement, "open_pipeline": sum(float(o.get("value", 0) or 0) for o in open_opportunities), "weighted": sum(float(o.get("value", 0) or 0) * float(o.get("probability", 0) or 0) / 100 for o in open_opportunities), "coverage": coverage, "won": won, "won_count": len(won_opportunities), "lost_count": len(lost_opportunities), "win_rate": win_rate, "po": len(orders), "po_value": sum(float(o.get("total", 0) or 0) for o in orders), "activities": len(activities), "overdue_activities": overdue_activities, "indent": len([o for o in orders if o.get("status") == "Indent"]), "overdue": overdue_orders})
    return result


@router.get("/options", response_model=OptionsResponse)
async def options(user: dict = Depends(current_user)):
    customers = await db.customers.find({}, {"id": 1, "name": 1}).sort("name", 1).to_list(1000)
    products = await db.products.find({}, {"id": 1, "name": 1, "default_price": 1}).sort("name", 1).to_list(1000)
    role = str(user.get("role") or "").strip().upper()
    if role == "SUPER_ADMIN":
        users = await db.users.find({}, {"id": 1, "user_id": 1, "name": 1, "role": 1}).sort("name", 1).to_list(100)
    else:
        users = await db.users.find({"id": {"$in": await manager_user_ids(user)}}, {"id": 1, "user_id": 1, "name": 1, "role": 1}).sort("name", 1).to_list(100)
    return {"customers": customers, "products": products, "users": users}


@router.get("/exports/{module}")
async def export_csv(module: str, user: dict = Depends(current_user)):
    import csv
    import io
    from fastapi.responses import Response

    allowed = {"customers": "customers", "pipeline": "opportunities", "activities": "activities", "quotations": "quotations", "purchase-orders": "purchase_orders", "products": "products", "sales-team": "users"}
    collection = allowed.get(module)
    if not collection:
        raise HTTPException(status_code=404, detail="Modul export tidak ditemukan")

    role = str(user.get("role") or "").strip().upper()
    filters: dict = {}
    visible_ids = await visible_sales_ids(user)
    if module in {"pipeline", "activities", "quotations", "purchase-orders"}:
        filters = {"sales_id": {"$in": visible_ids}}
    elif module == "customers" and role != "SUPER_ADMIN":
        filters = {"sales_id": {"$in": visible_ids}}
    elif module == "sales-team":
        filters = {"id": {"$in": (await manager_user_ids(user) if role == "SALES_MANAGER" else visible_ids)}}

    docs = await db[collection].find(filters, {"_id": 0, "password_hash": 0, "content": 0}).limit(5000).to_list(5000)
    if not docs:
        return Response("", media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={module}.csv"})

    fields = sorted({key for doc in docs for key, value in doc.items() if not isinstance(value, (list, dict))})
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(docs)
    await audit(user, "Export", module.title())
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={module}.csv"})
