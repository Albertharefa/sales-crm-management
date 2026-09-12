from fastapi import APIRouter, Depends, HTTPException, Query
from lib.db import db
from models.crm import Paginated
from routers.common import page_collection
from routers.customers import ensure_customer_access
from routers.deps import current_user

router = APIRouter(prefix="/order-monitoring", tags=["order-monitoring"])


def role_name(user: dict) -> str:
    return str(user.get("role") or "").strip().upper()


async def visible_sales_ids(user: dict) -> list[str]:
    role = role_name(user)
    if role == "SUPER_ADMIN":
        docs = await db.users.find({"role": "SALES", "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]}}, {"_id": 0, "id": 1}).to_list(1000)
        return [str(d["id"]) for d in docs if d.get("id")]
    if role == "SALES_MANAGER":
        docs = await db.users.find({"manager_id": user.get("id"), "role": "SALES", "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]}}, {"_id": 0, "id": 1}).to_list(1000)
        return [str(d["id"]) for d in docs if d.get("id")]
    if role == "SALES":
        return [str(user.get("id"))]
    return []


@router.get("", response_model=Paginated)
async def list_order_monitoring(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    status: str | None = None,
    sales: str | None = None,
    customer_id: str | None = None,
    user: dict = Depends(current_user),
):
    if role_name(user) not in {"SUPER_ADMIN", "SALES_MANAGER", "SALES"}:
        raise HTTPException(status_code=403, detail="Role Anda tidak memiliki akses Order Monitoring")

    visible_ids = await visible_sales_ids(user)
    customers = await db.customers.find({}, {"_id": 0, "id": 1, "customer_id": 1}).to_list(10000)
    valid_customer_ids = {str(c[k]) for c in customers for k in ("id", "customer_id") if c.get(k)}

    filters: dict = {
        "customer_id": {"$in": list(valid_customer_ids)},
        "sales_id": {"$in": visible_ids},
    }
    if status:
        filters["status"] = status
    if sales:
        sales_user = await db.users.find_one({"name": sales, "id": {"$in": visible_ids}}, {"_id": 0, "id": 1})
        if not sales_user:
            raise HTTPException(status_code=403, detail="Sales berada di luar scope Anda")
        filters["sales_id"] = sales_user["id"]
    if customer_id:
        customer = await db.customers.find_one({"id": customer_id}) or await db.customers.find_one({"customer_id": customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
        await ensure_customer_access(customer, user)
        filters["customer_id"] = str(customer.get("id") or customer_id)

    return await page_collection("purchase_orders", page, page_size, search, filters)


@router.get("/summary")
async def order_monitoring_summary(
    search: str = "",
    status: str | None = None,
    sales: str | None = None,
    customer_id: str | None = None,
    user: dict = Depends(current_user),
):
    if role_name(user) not in {"SUPER_ADMIN", "SALES_MANAGER", "SALES"}:
        raise HTTPException(status_code=403, detail="Role Anda tidak memiliki akses Order Monitoring")
    visible_ids = await visible_sales_ids(user)
    customers = await db.customers.find({}, {"_id": 0, "id": 1, "customer_id": 1}).to_list(10000)
    valid_customer_ids = {str(c[k]) for c in customers for k in ("id", "customer_id") if c.get(k)}
    filters: dict = {"customer_id": {"$in": list(valid_customer_ids)}, "sales_id": {"$in": visible_ids}}
    if status:
        if status not in {"Received", "Waiting Order", "Confirmed", "Processing", "Indent", "Ready Stock", "Delivery", "Completed", "Cancelled"}:
            raise HTTPException(status_code=422, detail="Status order tidak valid")
        filters["status"] = status
    if sales:
        sales_user = await db.users.find_one({"name": sales, "id": {"$in": visible_ids}}, {"_id": 0, "id": 1})
        if not sales_user:
            raise HTTPException(status_code=403, detail="Sales berada di luar scope Anda")
        filters["sales_id"] = sales_user["id"]
    if customer_id:
        customer = await db.customers.find_one({"id": customer_id}) or await db.customers.find_one({"customer_id": customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
        await ensure_customer_access(customer, user)
        filters["customer_id"] = str(customer.get("id") or customer_id)
    if search.strip():
        term = search.strip()
        filters["$or"] = [
            {"po_number": {"$regex": term, "$options": "i"}},
            {"customer_name": {"$regex": term, "$options": "i"}},
            {"sales_name": {"$regex": term, "$options": "i"}},
            {"items.description": {"$regex": term, "$options": "i"}},
        ]
    counts = {"TOTAL": await db.purchase_orders.count_documents(filters)}
    for stage in ["Received", "Waiting Order", "Processing", "Indent", "Ready Stock", "Delivery", "Completed", "Cancelled"]:
        stage_filter = {**filters, "status": stage}
        counts[stage.upper()] = await db.purchase_orders.count_documents(stage_filter)
    return counts
