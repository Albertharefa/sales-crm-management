from fastapi import APIRouter, Depends, HTTPException, Query
from lib.db import db
from models.crm import Paginated, PurchaseOrder, PurchaseOrderCreate
from routers.common import audit, new_id, now, page_collection
from routers.deps import current_user
from routers.customers import ensure_customer_access

router = APIRouter(prefix="/purchase-orders", tags=["orders"])
ORDER_STAGES = ["Received", "Waiting Order", "Confirmed", "Processing", "Indent", "Ready Stock", "Delivery", "Completed", "Cancelled"]
ALL_STATUSES = ["Draft", *ORDER_STAGES]


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


async def validate_sales_assignment(sales_id: str, user: dict) -> dict:
    sales = await db.users.find_one({"id": sales_id, "role": "SALES"}, {"_id": 0, "id": 1, "name": 1, "status": 1, "manager_id": 1})
    if not sales:
        raise HTTPException(status_code=400, detail="Sales tidak valid")
    if str(sales.get("status") or "Active").upper() in {"INACTIVE", "DISABLED"}:
        raise HTTPException(status_code=400, detail="Sales tidak aktif")
    role = role_name(user)
    if role == "SALES" and str(sales["id"]) != str(user.get("id")):
        raise HTTPException(status_code=403, detail="Sales hanya dapat menggunakan akun sendiri")
    if role == "SALES_MANAGER" and str(sales.get("manager_id")) != str(user.get("id")):
        raise HTTPException(status_code=403, detail="Sales tersebut bukan anggota team Anda")
    if role not in {"SUPER_ADMIN", "SALES_MANAGER", "SALES"}:
        raise HTTPException(status_code=403, detail="Role Anda tidak memiliki akses Purchase Order")
    return sales


async def ensure_access(doc: dict, user: dict) -> None:
    role = role_name(user)
    if role == "SUPER_ADMIN":
        return
    sales_id = str(doc.get("sales_id") or "")
    if role == "SALES" and sales_id == str(user.get("id")):
        return
    if role == "SALES_MANAGER" and sales_id in await visible_sales_ids(user):
        return
    raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke PO ini")


async def find_customer(customer_ref: str):
    ref = str(customer_ref or "").strip()
    if not ref:
        return None
    customer = await db.customers.find_one({"id": ref})
    return customer or await db.customers.find_one({"customer_id": ref})


async def validate_quotation_link(quotation_number: str | None, customer: dict, sales: dict, user: dict) -> dict | None:
    number = str(quotation_number or "").strip()
    if not number:
        return None
    quotation = await db.quotations.find_one({"number": number}, {"_id": 0})
    if not quotation:
        raise HTTPException(status_code=400, detail="Quotation tidak ditemukan")
    await ensure_quotation_access(quotation, user)
    quotation_customer = str(quotation.get("customer_id") or "")
    canonical_customer = str(customer.get("id") or customer.get("customer_id") or "")
    if quotation_customer and quotation_customer != canonical_customer:
        linked_customer = await find_customer(quotation_customer)
        linked_canonical = str((linked_customer or {}).get("id") or (linked_customer or {}).get("customer_id") or quotation_customer)
        if linked_canonical != canonical_customer:
            raise HTTPException(status_code=409, detail="Customer PO tidak sama dengan Customer pada quotation")
    quotation_sales = str(quotation.get("sales_id") or "")
    if quotation_sales and quotation_sales != str(sales.get("id")):
        raise HTTPException(status_code=409, detail="Sales PO tidak sama dengan Sales pada quotation")
    return quotation


async def ensure_quotation_access(doc: dict, user: dict) -> None:
    role = role_name(user)
    if role == "SUPER_ADMIN":
        return
    sales_id = str(doc.get("sales_id") or "")
    if role == "SALES" and sales_id == str(user.get("id")):
        return
    if role == "SALES_MANAGER" and sales_id in await visible_sales_ids(user):
        return
    raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke quotation ini")


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


async def validate_product_items(items) -> None:
    product_ids = {str(item.product_id).strip() for item in items if item.product_id}
    if not product_ids:
        return
    found = await db.products.find({"id": {"$in": list(product_ids)}}, {"_id": 0, "id": 1}).to_list(1000)
    found_ids = {str(item.get("id")) for item in found if item.get("id")}
    missing = sorted(product_ids - found_ids)
    if missing:
        raise HTTPException(status_code=400, detail=f"Produk tidak ditemukan: {', '.join(missing)}")


async def quotation_total(quotation_number: str | None, fallback: float):
    if quotation_number:
        quotation = await db.quotations.find_one({"number": quotation_number}, {"_id": 0, "grand_total": 1})
        if quotation and quotation.get("grand_total") is not None:
            return float(quotation["grand_total"])
    return fallback


@router.get("", response_model=Paginated)
async def list_orders(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", status: str | None = None, sales: str | None = None, customer: str | None = None, user: dict = Depends(current_user)):
    if role_name(user) not in {"SUPER_ADMIN", "SALES_MANAGER", "SALES"}:
        raise HTTPException(status_code=403, detail="Role Anda tidak memiliki akses Purchase Order")
    visible_ids = await visible_sales_ids(user)
    filters: dict = {"sales_id": {"$in": visible_ids}}
    if status:
        if status not in ALL_STATUSES:
            raise HTTPException(status_code=422, detail="Status order tidak valid")
        filters["status"] = status
    if sales:
        sales_user = await db.users.find_one({"name": sales, "id": {"$in": visible_ids}}, {"_id": 0, "id": 1})
        if not sales_user:
            raise HTTPException(status_code=403, detail="Sales berada di luar scope Anda")
        filters["sales_id"] = sales_user["id"]
    if customer:
        customer_doc = await find_customer(customer)
        if not customer_doc:
            raise HTTPException(status_code=403, detail="Customer berada di luar scope Anda")
        await ensure_customer_access(customer_doc, user)
        filters["customer_id"] = str(customer_doc.get("id") or customer_doc.get("customer_id"))
    return await page_collection("purchase_orders", page, page_size, search, filters)


@router.get("/quotation-options")
async def quotation_options(search: str = Query("", max_length=100), limit: int = Query(50, ge=1, le=100), user: dict = Depends(current_user)):
    """Return quotations available to the logged-in sales scope for PO linking."""
    if role_name(user) not in {"SUPER_ADMIN", "SALES_MANAGER", "SALES"}:
        raise HTTPException(status_code=403, detail="Role Anda tidak memiliki akses Purchase Order")
    visible_ids = await visible_sales_ids(user)
    filters: dict = {"sales_id": {"$in": visible_ids}}
    term = search.strip()
    if term:
        filters["$or"] = [
            {"number": {"$regex": term, "$options": "i"}},
            {"customer_name": {"$regex": term, "$options": "i"}},
        ]
    docs = await db.quotations.find(filters, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return docs


@router.post("", response_model=PurchaseOrder)
async def create_order(payload: PurchaseOrderCreate, user: dict = Depends(current_user)):
    customer = await find_customer(payload.customer_id)
    if not customer:
        raise HTTPException(status_code=400, detail="Customer tidak valid")
    await ensure_customer_access(customer, user)
    await validate_product_items(payload.items)
    if payload.status not in ALL_STATUSES:
        raise HTTPException(status_code=422, detail="Status order tidak valid")
    po_number = payload.po_number.strip()
    if not po_number:
        raise HTTPException(status_code=422, detail="Nomor PO wajib diisi")
    if await db.purchase_orders.find_one({"po_number": po_number}, {"_id": 1}):
        raise HTTPException(status_code=409, detail="Nomor PO sudah digunakan")
    sales_id = payload.sales_id or user.get("id")
    sales = await validate_sales_assignment(str(sales_id), user)
    quotation = None if payload.quotation_manual else await validate_quotation_link(payload.quotation_number, customer, sales, user)
    raw_total = calculate_total(payload)
    total = float(quotation.get("grand_total")) if quotation and quotation.get("grand_total") is not None else raw_total
    payload_data = payload.model_dump(mode="json")
    payload_data["po_number"] = po_number
    payload_data["customer_id"] = str(customer.get("id") or customer.get("customer_id"))
    payload_data["sales_id"] = str(sales["id"])
    if quotation:
        payload_data["quotation_number"] = quotation["number"]
    doc = {"id": new_id(), "customer_name": customer.get("name") or customer.get("company_name") or "", "sales_name": sales["name"], "total": total, **payload_data, "created_at": now()}
    await db.purchase_orders.insert_one(doc)
    await audit(user, "Create", "Purchase Orders", doc["id"], {"po_number": doc["po_number"], "quotation_number": doc.get("quotation_number"), "quotation_manual": doc.get("quotation_manual", False)})
    return PurchaseOrder(**doc)


@router.get("/{order_id}", response_model=PurchaseOrder)
async def get_order(order_id: str, user: dict = Depends(current_user)):
    doc = await db.purchase_orders.find_one({"id": order_id})
    if not doc:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    await ensure_access(doc, user)
    doc.pop("_id", None)
    customer = await find_customer(str(doc.get("customer_id") or ""))
    if not customer and doc.get("customer_name"):
        customer = await db.customers.find_one({"name": doc["customer_name"]}, {"_id": 0, "customer_id": 1, "id": 1, "name": 1})
    if customer:
        doc["customer_id"] = str(customer.get("id") or customer.get("customer_id") or doc.get("customer_id"))
        doc["customer_name"] = customer.get("name") or customer.get("company_name") or doc.get("customer_name") or ""
    if doc.get("quotation_number") and not doc.get("quotation_manual"):
        doc["total"] = await quotation_total(doc.get("quotation_number"), float(doc.get("total") or 0))
    elif doc.get("items"):
        doc["total"] = calculate_items_total(doc["items"])
    return PurchaseOrder(**doc)


@router.put("/{order_id}", response_model=PurchaseOrder)
async def update_order(order_id: str, payload: PurchaseOrderCreate, user: dict = Depends(current_user)):
    old = await db.purchase_orders.find_one({"id": order_id})
    if not old:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    await ensure_access(old, user)
    customer = await find_customer(payload.customer_id)
    if not customer:
        raise HTTPException(status_code=400, detail="Customer tidak valid")
    await ensure_customer_access(customer, user)
    await validate_product_items(payload.items)
    if payload.status not in ALL_STATUSES:
        raise HTTPException(status_code=422, detail="Status order tidak valid")
    po_number = payload.po_number.strip()
    if not po_number:
        raise HTTPException(status_code=422, detail="Nomor PO wajib diisi")
    duplicate = await db.purchase_orders.find_one({"po_number": po_number, "id": {"$ne": order_id}}, {"_id": 1})
    if duplicate:
        raise HTTPException(status_code=409, detail="Nomor PO sudah digunakan")
    sales_id = payload.sales_id or old.get("sales_id") or user.get("id")
    sales = await validate_sales_assignment(str(sales_id), user)
    quotation = None if payload.quotation_manual else await validate_quotation_link(payload.quotation_number, customer, sales, user)
    total = float(quotation.get("grand_total")) if quotation and quotation.get("grand_total") is not None else calculate_total(payload)
    payload_data = payload.model_dump(mode="json")
    payload_data["po_number"] = po_number
    payload_data["customer_id"] = str(customer.get("id") or customer.get("customer_id"))
    payload_data["sales_id"] = str(sales["id"])
    if quotation:
        payload_data["quotation_number"] = quotation["number"]
    doc = {"id": order_id, "customer_name": customer.get("name") or customer.get("company_name") or "", "sales_name": sales["name"], "total": total, **payload_data, "created_at": old.get("created_at", now()), "updated_at": now()}
    await db.purchase_orders.replace_one({"id": order_id}, doc)
    await audit(user, "Update", "Purchase Orders", order_id, {"po_number": doc["po_number"], "quotation_number": doc.get("quotation_number"), "quotation_manual": doc.get("quotation_manual", False)})
    return PurchaseOrder(**doc)


@router.delete("/{order_id}")
async def delete_order(order_id: str, user: dict = Depends(current_user)):
    doc = await db.purchase_orders.find_one({"id": order_id})
    if not doc:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    await ensure_access(doc, user)
    if doc.get("status") == "Completed":
        raise HTTPException(status_code=409, detail="PO yang sudah Completed tidak dapat dihapus")
    await db.purchase_orders.delete_one({"id": order_id})
    await audit(user, "Delete", "Purchase Orders", order_id, {"po_number": doc.get("po_number")})
    return {"ok": True}


@router.patch("/{order_id}/status", response_model=PurchaseOrder)
async def update_order_status(order_id: str, status: str, user: dict = Depends(current_user)):
    if status not in ALL_STATUSES:
        raise HTTPException(status_code=422, detail="Status order tidak valid")
    doc = await db.purchase_orders.find_one({"id": order_id})
    if not doc:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    await ensure_access(doc, user)
    updated_at = now()
    await db.purchase_orders.update_one({"id": order_id}, {"$set": {"status": status, "updated_at": updated_at}})
    updated = {**doc, "status": status, "updated_at": updated_at}
    updated.pop("_id", None)
    await audit(user, "Status Change", "Purchase Orders", order_id, {"status": status})
    return PurchaseOrder(**updated)
