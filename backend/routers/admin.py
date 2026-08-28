from fastapi import APIRouter, Depends, HTTPException, Query
from passlib.context import CryptContext
from lib.db import db
from models.crm import Paginated, UserCreate, UserPublic, OptionsResponse, SalesTeamMetric
from routers.common import audit, new_id, now, page_collection
from routers.deps import current_user

router = APIRouter(tags=["admin"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/users", response_model=Paginated)
async def list_users(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", user: dict = Depends(current_user)):
    return await page_collection("users", page, page_size, search)


@router.post("/users", response_model=UserPublic)
async def create_user(payload: UserCreate, user: dict = Depends(current_user)):
    if user.get("role") not in ["SUPER_ADMIN"]:
        raise HTTPException(status_code=403, detail="Hanya Super Admin")
    if await db.users.find_one({"email": payload.email.lower()}):
        raise HTTPException(status_code=409, detail="Email sudah terdaftar")
    doc = {"id": new_id(), "user_id": f"USR-{await db.users.count_documents({}) + 1:04d}", "email": payload.email.lower(), "password_hash": pwd_context.hash(payload.password), **payload.model_dump(mode="json", exclude={"password"}), "created_at": now()}
    await db.users.insert_one(doc)
    await audit(user, "Create", "Users", doc["id"], {"email": doc["email"]})
    return UserPublic(**doc)


@router.get("/audit-logs", response_model=Paginated)
async def list_audit_logs(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", user: dict = Depends(current_user)):
    return await page_collection("audit_logs", page, page_size, search)


@router.get("/sales-team", response_model=list[SalesTeamMetric])
async def sales_team(user: dict = Depends(current_user)):
    users = await db.users.find({"role": {"$in": ["SALES", "SALES_MANAGER"]}}).to_list(100)
    result = []
    for person in users:
        opportunities = await db.opportunities.find({"sales_id": person["id"]}).to_list(1000)
        orders = await db.purchase_orders.find({"sales_name": person["name"]}).to_list(1000)
        result.append({"sales": person["name"], "role": person["role"], "manager": person.get("manager_id") or "-", "open_pipeline": sum(o.get("value", 0) for o in opportunities if o.get("stage") not in ["Won", "Lost"]), "weighted": sum(o.get("value", 0) * o.get("probability", 0) / 100 for o in opportunities if o.get("stage") not in ["Won", "Lost"]), "won": sum(o.get("value", 0) for o in opportunities if o.get("stage") == "Won"), "po": len(orders), "po_value": sum(o.get("total", 0) for o in orders), "activities": await db.activities.count_documents({"sales_id": person["id"]}), "indent": len([o for o in orders if o.get("status") == "Indent"]), "overdue": 0})
    return result


@router.get("/options", response_model=OptionsResponse)
async def options(user: dict = Depends(current_user)):
    customers = await db.customers.find({}, {"id": 1, "name": 1}).sort("name", 1).to_list(1000)
    products = await db.products.find({}, {"id": 1, "name": 1, "default_price": 1}).sort("name", 1).to_list(1000)
    users = await db.users.find({}, {"id": 1, "name": 1, "role": 1}).sort("name", 1).to_list(100)
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
    docs = await db[collection].find({}, {"_id": 0, "password_hash": 0, "content": 0}).limit(5000).to_list(5000)
    if not docs:
        return Response("", media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={module}.csv"})
    fields = sorted({key for doc in docs for key, value in doc.items() if not isinstance(value, (list, dict))})
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(docs)
    await audit(user, "Export", module.title())
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={module}.csv"})