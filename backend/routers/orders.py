from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from lib.db import db
from models.crm import Paginated, PurchaseOrder, PurchaseOrderCreate
from routers.common import audit, new_id, now, page_collection
from routers.deps import current_user

router = APIRouter(prefix="/purchase-orders", tags=["orders"])
ORDER_STAGES = ["Received", "Processing", "Indent", "Ready Stock", "Delivery", "Completed"]


@router.get("", response_model=Paginated)
async def list_orders(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", status: str | None = None, user: dict = Depends(current_user)):
    return await page_collection("purchase_orders", page, page_size, search, {"status": status} if status else {})


@router.post("", response_model=PurchaseOrder)
async def create_order(payload: PurchaseOrderCreate, user: dict = Depends(current_user)):
    customer = await db.customers.find_one({"id": payload.customer_id})
    if not customer:
        raise HTTPException(status_code=400, detail="Customer tidak valid")
    total = sum(i.quantity * i.unit_price for i in payload.items)
    doc = {"id": new_id(), "customer_name": customer["name"], "sales_name": user["name"], "total": total, **payload.model_dump(mode="json"), "created_at": now()}
    await db.purchase_orders.insert_one(doc)
    await audit(user, "Create", "Purchase Orders", doc["id"], {"po_number": doc["po_number"]})
    return PurchaseOrder(**doc)


@router.get("/monitoring", response_model=Paginated)
async def monitoring(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", status: str | None = None, user: dict = Depends(current_user)):
    return await page_collection("purchase_orders", page, page_size, search, {"status": status} if status else {})


@router.patch("/{order_id}/status", response_model=PurchaseOrder)
async def update_order_status(order_id: str, status: str, user: dict = Depends(current_user)):
    if status not in ORDER_STAGES and status not in ["Draft", "Cancelled"]:
        raise HTTPException(status_code=422, detail="Status order tidak valid")
    doc = await db.purchase_orders.find_one({"id": order_id})
    if not doc:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    await db.purchase_orders.update_one({"id": order_id}, {"$set": {"status": status}})
    await audit(user, "Status Change", "Purchase Orders", order_id, {"status": status})
    return PurchaseOrder(**{**doc, "status": status})