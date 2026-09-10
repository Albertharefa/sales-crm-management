from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from lib.db import db
from models.crm import Paginated, PurchaseOrder, PurchaseOrderCreate
from routers.common import audit, new_id, now, page_collection
from routers.deps import current_user

router = APIRouter(prefix="/purchase-orders", tags=["orders"])
ORDER_STAGES = ["Received", "Confirmed", "Processing", "Completed"]


@router.get("", response_model=Paginated)
async def list_orders(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", status: str | None = None, sales: str | None = None, user: dict = Depends(current_user)):
    filters = {}
    if status:
        filters["status"] = status
    if sales:
        filters["sales_name"] = sales
    return await page_collection("purchase_orders", page, page_size, search, filters)


@router.post("", response_model=PurchaseOrder)
async def create_order(payload: PurchaseOrderCreate, user: dict = Depends(current_user)):
    customer = await db.customers.find_one({"id": payload.customer_id})
    if not customer:
        raise HTTPException(status_code=400, detail="Customer tidak valid")
    total = sum(i.quantity * i.unit_price for i in payload.items)
    sales_name = user["name"]
    if payload.sales_id:
        sales_user = await db.users.find_one({"id": payload.sales_id}, {"_id": 0, "id": 1, "name": 1})
        if not sales_user:
            raise HTTPException(status_code=400, detail="Sales tidak valid")
        sales_name = sales_user["name"]
    doc = {"id": new_id(), "customer_name": customer["name"], "sales_name": sales_name, "total": total, **payload.model_dump(mode="json"), "created_at": now()}
    await db.purchase_orders.insert_one(doc)
    await audit(user, "Create", "Purchase Orders", doc["id"], {"po_number": doc["po_number"]})
    return PurchaseOrder(**doc)


@router.get("/{order_id}", response_model=PurchaseOrder)
async def get_order(order_id: str, user: dict = Depends(current_user)):
    doc = await db.purchase_orders.find_one({"id": order_id})
    if not doc:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    doc.pop("_id", None)

    # Gunakan Customer ID resmi dari master customer untuk tampilan detail PO.
    # PO lama bisa saja menyimpan UUID/internal ID, jadi kita resolve kembali
    # ke data customer berdasarkan id, customer_id, atau nama customer.
    stored_customer_id = str(doc.get("customer_id") or "").strip()
    customer = None

    if stored_customer_id:
        customer = await db.customers.find_one(
            {"id": stored_customer_id},
            {"_id": 0, "customer_id": 1, "id": 1, "name": 1},
        )

        if not customer:
            customer = await db.customers.find_one(
                {"customer_id": stored_customer_id},
                {"_id": 0, "customer_id": 1, "id": 1, "name": 1},
            )

    if not customer and doc.get("customer_name"):
        customer = await db.customers.find_one(
            {"name": doc["customer_name"]},
            {"_id": 0, "customer_id": 1, "id": 1, "name": 1},
        )

    if customer:
        doc["customer_id"] = str(
            customer.get("customer_id")
            or customer.get("id")
            or stored_customer_id
        )

    return PurchaseOrder(**doc)


@router.put("/{order_id}", response_model=PurchaseOrder)
async def update_order(order_id: str, payload: PurchaseOrderCreate, user: dict = Depends(current_user)):
    customer = await db.customers.find_one({"id": payload.customer_id})
    if not customer:
        raise HTTPException(status_code=400, detail="Customer tidak valid")
    old = await db.purchase_orders.find_one({"id": order_id})
    if not old:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    total = sum(i.quantity * i.unit_price for i in payload.items)
    sales_name = old.get("sales_name", user["name"])
    if payload.sales_id:
        sales_user = await db.users.find_one({"id": payload.sales_id}, {"_id": 0, "id": 1, "name": 1})
        if not sales_user:
            raise HTTPException(status_code=400, detail="Sales tidak valid")
        sales_name = sales_user["name"]
    doc = {"id": order_id, "customer_name": customer["name"], "sales_name": sales_name, "total": total, **payload.model_dump(mode="json"), "created_at": old.get("created_at", now())}
    await db.purchase_orders.replace_one({"id": order_id}, doc)
    await audit(user, "Update", "Purchase Orders", order_id, {"po_number": doc["po_number"]})
    return PurchaseOrder(**doc)


@router.delete("/{order_id}")
async def delete_order(order_id: str, user: dict = Depends(current_user)):
    doc = await db.purchase_orders.find_one({"id": order_id})
    if not doc:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    await db.purchase_orders.delete_one({"id": order_id})
    await audit(user, "Delete", "Purchase Orders", order_id, {"po_number": doc.get("po_number")})
    return {"ok": True}


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