from fastapi import APIRouter, Depends, HTTPException, Query
from lib.db import db
from models.crm import Paginated, PurchaseOrder, PurchaseOrderCreate
from routers.common import audit, new_id, now, page_collection
from routers.deps import current_user

router = APIRouter(prefix="/purchase-orders", tags=["orders"])
ORDER_STAGES = ["Received", "Confirmed", "Processing", "Completed"]

def calculate_total(payload):
    total = 0.0
    for item in payload.items:
        gross = max(0.0, float(item.quantity) * float(item.unit_price))
        discount = max(0.0, float(getattr(item, "discount", 0) or 0))
        net = max(0.0, gross - discount)
        tax = max(0.0, float(getattr(item, "tax", 0) or 0))
        total += net + (net * tax / 100.0)
    return total

def calculate_items_total(items):
    total = 0.0
    for item in items or []:
        gross = max(0.0, float(item.get("quantity") or 0) * float(item.get("unit_price") or 0))
        discount = max(0.0, float(item.get("discount") or 0))
        net = max(0.0, gross - discount)
        tax = max(0.0, float(item.get("tax") or 0))
        total += net + (net * tax / 100.0)
    return total

async def quotation_total(quotation_number: str | None, fallback: float):
    if quotation_number:
        quotation = await db.quotations.find_one({"number": quotation_number}, {"_id": 0, "grand_total": 1})
        if quotation and quotation.get("grand_total") is not None:
            return float(quotation["grand_total"])
    return fallback

@router.get("", response_model=Paginated)
async def list_orders(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", status: str | None = None, sales: str | None = None, user: dict = Depends(current_user)):
    filters = {}
    if status: filters["status"] = status
    if sales: filters["sales_name"] = sales
    return await page_collection("purchase_orders", page, page_size, search, filters)

@router.post("", response_model=PurchaseOrder)
async def create_order(payload: PurchaseOrderCreate, user: dict = Depends(current_user)):
    customer = await db.customers.find_one({"id": payload.customer_id})
    if not customer: raise HTTPException(status_code=400, detail="Customer tidak valid")
    raw_total = calculate_total(payload)
    total = raw_total
    if payload.quotation_number and all(("discount" not in item or "tax" not in item) for item in payload.items):
        total = await quotation_total(payload.quotation_number, raw_total)
    sales_name = user["name"]
    if payload.sales_id:
        sales_user = await db.users.find_one({"id": payload.sales_id}, {"_id": 0, "id": 1, "name": 1})
        if not sales_user: raise HTTPException(status_code=400, detail="Sales tidak valid")
        sales_name = sales_user["name"]
    doc = {"id": new_id(), "customer_name": customer["name"], "sales_name": sales_name, "total": total, **payload.model_dump(mode="json"), "created_at": now()}
    await db.purchase_orders.insert_one(doc)
    await audit(user, "Create", "Purchase Orders", doc["id"], {"po_number": doc["po_number"]})
    return PurchaseOrder(**doc)

@router.get("/{order_id}", response_model=PurchaseOrder)
async def get_order(order_id: str, user: dict = Depends(current_user)):
    doc = await db.purchase_orders.find_one({"id": order_id})
    if not doc: raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    doc.pop("_id", None)
    stored_customer_id = str(doc.get("customer_id") or "").strip()
    customer = None
    if stored_customer_id:
        customer = await db.customers.find_one({"id": stored_customer_id}, {"_id": 0, "customer_id": 1, "id": 1, "name": 1})
        if not customer: customer = await db.customers.find_one({"customer_id": stored_customer_id}, {"_id": 0, "customer_id": 1, "name": 1})
    if not customer and doc.get("customer_name"):
        customer = await db.customers.find_one({"name": doc["customer_name"]}, {"_id": 0, "customer_id": 1, "id": 1, "name": 1})
    if customer: doc["customer_id"] = str(customer.get("customer_id") or customer.get("id") or stored_customer_id)
    if doc.get("quotation_number") and not all(("discount" in item and "tax" in item) for item in (doc.get("items") or [])):
        doc["total"] = await quotation_total(doc.get("quotation_number"), float(doc.get("total") or 0))
    elif doc.get("items"):
        doc["total"] = calculate_items_total(doc["items"])
    return PurchaseOrder(**doc)

@router.put("/{order_id}", response_model=PurchaseOrder)
async def update_order(order_id: str, payload: PurchaseOrderCreate, user: dict = Depends(current_user)):
    customer = await db.customers.find_one({"id": payload.customer_id})
    if not customer: raise HTTPException(status_code=400, detail="Customer tidak valid")
    old = await db.purchase_orders.find_one({"id": order_id})
    if not old: raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    total = calculate_total(payload)
    sales_name = old.get("sales_name", user["name"])
    if payload.sales_id:
        sales_user = await db.users.find_one({"id": payload.sales_id}, {"_id": 0, "id": 1, "name": 1})
        if not sales_user: raise HTTPException(status_code=400, detail="Sales tidak valid")
        sales_name = sales_user["name"]
    doc = {"id": order_id, "customer_name": customer["name"], "sales_name": sales_name, "total": total, **payload.model_dump(mode="json"), "created_at": old.get("created_at", now())}
    await db.purchase_orders.replace_one({"id": order_id}, doc)
    await audit(user, "Update", "Purchase Orders", order_id, {"po_number": doc["po_number"]})
    return PurchaseOrder(**doc)

@router.delete("/{order_id}")
async def delete_order(order_id: str, user: dict = Depends(current_user)):
    doc = await db.purchase_orders.find_one({"id": order_id})
    if not doc: raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    await db.purchase_orders.delete_one({"id": order_id})
    await audit(user, "Delete", "Purchase Orders", order_id, {"po_number": doc.get("po_number")})
    return {"ok": True}

@router.get("/monitoring", response_model=Paginated)
async def monitoring(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", status: str | None = None, user: dict = Depends(current_user)):
    return await page_collection("purchase_orders", page, page_size, search, {"status": status} if status else {})

@router.patch("/{order_id}/status", response_model=PurchaseOrder)
async def update_order_status(order_id: str, status: str, user: dict = Depends(current_user)):
    if status not in ORDER_STAGES and status not in ["Draft", "Cancelled"]: raise HTTPException(status_code=422, detail="Status order tidak valid")
    doc = await db.purchase_orders.find_one({"id": order_id})
    if not doc: raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    await db.purchase_orders.update_one({"id": order_id}, {"$set": {"status": status}})
    await audit(user, "Status Change", "Purchase Orders", order_id, {"status": status})
    return PurchaseOrder(**{**doc, "status": status})
