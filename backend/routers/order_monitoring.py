from datetime import datetime, timezone
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Query
from lib.db import db
from models.crm import Paginated
from routers.common import page_collection
from routers.customers import ensure_customer_access
from routers.deps import current_user

router = APIRouter(prefix="/order-monitoring", tags=["order-monitoring"])

SALES_ROLES = {"SUPER_ADMIN", "SALES_MANAGER", "SALES"}
STAGES = ["Received", "Waiting Order", "Processing", "Indent", "Ready Stock", "Delivery", "Completed", "Cancelled"]
_CACHE_TTL = 30.0
_sales_cache: dict[str, tuple[float, list[str]]] = {}
_customer_ids_cache: tuple[float, set[str]] | None = None


def role_name(user: dict) -> str:
    return str(user.get("role") or "").strip().upper()


def build_eta_filter(value: str) -> dict:
    indicator = value.strip()
    if indicator not in {"Overdue", "Due Soon", "Selesai"}:
        raise HTTPException(status_code=422, detail="Indikator ETA tidak valid")
    if indicator == "Selesai":
        return {"status": "Completed"}
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    eta_date = {"$convert": {"input": "$eta", "to": "date", "onError": None, "onNull": None}}
    if indicator == "Overdue":
        return {"status": {"$nin": ["Completed", "Cancelled"]}, "$expr": {"$lt": [eta_date, today]}}
    return {"status": {"$ne": "Completed"}, "$or": [{"eta": {"$in": [None, ""]}}, {"$expr": {"$gte": [eta_date, today]}}]}


async def visible_sales_ids(user: dict) -> list[str]:
    role = role_name(user)
    if role == "SALES":
        return [str(user.get("id"))]
    if role not in {"SUPER_ADMIN", "SALES_MANAGER"}:
        return []
    key = f"{role}:{user.get('id') or ''}"
    now = monotonic()
    cached = _sales_cache.get(key)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]
    query = {"role": "SALES", "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]}}
    if role == "SALES_MANAGER":
        query["manager_id"] = user.get("id")
    docs = await db.users.find(query, {"_id": 0, "id": 1}).to_list(1000)
    ids = [str(d["id"]) for d in docs if d.get("id")]
    _sales_cache[key] = (now, ids)
    return ids


async def valid_customer_ids() -> set[str]:
    global _customer_ids_cache
    now = monotonic()
    if _customer_ids_cache and now - _customer_ids_cache[0] < _CACHE_TTL:
        return _customer_ids_cache[1]
    docs = await db.customers.find({}, {"_id": 0, "id": 1, "customer_id": 1}).to_list(10000)
    ids = {str(c[k]) for c in docs for k in ("id", "customer_id") if c.get(k)}
    _customer_ids_cache = (now, ids)
    return ids


async def build_filters(user: dict, status: str | None, sales: str | None, customer_id: str | None, eta_filter: str | None) -> dict:
    visible_ids = await visible_sales_ids(user)
    filters: dict = {"customer_id": {"$in": list(await valid_customer_ids())}, "sales_id": {"$in": visible_ids}}
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
    if eta_filter:
        filters.update(build_eta_filter(eta_filter))
    return filters


def add_search(filters: dict, search: str) -> None:
    if search.strip():
        term = search.strip()
        filters["$or"] = [
            {"po_number": {"$regex": term, "$options": "i"}},
            {"customer_name": {"$regex": term, "$options": "i"}},
            {"sales_name": {"$regex": term, "$options": "i"}},
            {"items.description": {"$regex": term, "$options": "i"}},
        ]


@router.get("", response_model=Paginated)
async def list_order_monitoring(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    status: str | None = None,
    sales: str | None = None,
    customer_id: str | None = None,
    eta_filter: str | None = None,
    user: dict = Depends(current_user),
):
    if role_name(user) not in SALES_ROLES:
        raise HTTPException(status_code=403, detail="Role Anda tidak memiliki akses Order Monitoring")
    filters = await build_filters(user, status, sales, customer_id, eta_filter)
    return await page_collection("purchase_orders", page, page_size, search, filters)


@router.get("/summary")
async def order_monitoring_summary(
    search: str = "",
    status: str | None = None,
    sales: str | None = None,
    customer_id: str | None = None,
    eta_filter: str | None = None,
    user: dict = Depends(current_user),
):
    if role_name(user) not in SALES_ROLES:
        raise HTTPException(status_code=403, detail="Role Anda tidak memiliki akses Order Monitoring")
    if status and status not in {"Received", "Waiting Order", "Confirmed", "Processing", "Indent", "Ready Stock", "Delivery", "Completed", "Cancelled"}:
        raise HTTPException(status_code=422, detail="Status order tidak valid")
    filters = await build_filters(user, status, sales, customer_id, eta_filter)
    add_search(filters, search)
    grouped = await db.purchase_orders.aggregate([
        {"$match": filters},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]).to_list(len(STAGES) + 5)
    counts = {"TOTAL": sum(int(row.get("count", 0)) for row in grouped)}
    counts.update({stage.upper(): 0 for stage in STAGES})
    for row in grouped:
        stage = str(row.get("_id") or "").upper()
        if stage in counts:
            counts[stage] = int(row.get("count", 0))
    return counts
