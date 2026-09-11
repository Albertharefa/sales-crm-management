from fastapi import APIRouter, Depends, Query

from lib.db import db
from models.crm import Paginated
from routers.common import page_collection
from routers.deps import current_user

router = APIRouter(prefix="/order-monitoring", tags=["order-monitoring"])


@router.get("", response_model=Paginated)
async def list_order_monitoring(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    status: str | None = None,
    sales: str | None = None,
    user: dict = Depends(current_user),
):
    customers = await db.customers.find(
        {}, {"_id": 0, "id": 1, "customer_id": 1}
    ).to_list(10000)
    valid_customer_ids = set()
    for customer in customers:
        if customer.get("id"):
            valid_customer_ids.add(str(customer["id"]))
        if customer.get("customer_id"):
            valid_customer_ids.add(str(customer["customer_id"]))

    filters = {
        "is_demo": {"$ne": True},
        "customer_id": {"$in": list(valid_customer_ids)},
    }
    if status:
        filters["status"] = status
    if sales:
        filters["sales_name"] = sales

    return await page_collection(
        "purchase_orders", page, page_size, search, filters
    )
