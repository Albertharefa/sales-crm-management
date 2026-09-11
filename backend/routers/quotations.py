from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from lib.db import db
from models.crm import Paginated, Quotation, QuotationCreate, QuotationUpdate
from routers.common import audit, new_id, next_number, now, page_collection
from routers.deps import current_user

router = APIRouter(prefix="/quotations", tags=["quotations"])

STATUS_OPTIONS = ["Draft", "Sent", "Negotiation", "Approved", "Rejected", "Expired", "Converted"]


def role_name(user: dict) -> str:
    return str(user.get("role") or "").strip().upper()


async def visible_sales_ids(user: dict) -> list[str]:
    role = role_name(user)
    if role == "SUPER_ADMIN":
        docs = await db.users.find(
            {"role": "SALES", "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]}},
            {"_id": 0, "id": 1},
        ).to_list(1000)
        return [str(d["id"]) for d in docs if d.get("id")]
    if role == "SALES_MANAGER":
        docs = await db.users.find(
            {"manager_id": user.get("id"), "role": "SALES", "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]}},
            {"_id": 0, "id": 1},
        ).to_list(1000)
        return [str(d["id"]) for d in docs if d.get("id")]
    if role == "SALES":
        return [str(user.get("id"))]
    return []


async def validate_sales_assignment(sales_id: str, user: dict) -> dict:
    sales = await db.users.find_one(
        {"id": sales_id, "role": "SALES"},
        {"_id": 0, "id": 1, "user_id": 1, "name": 1, "role": 1, "status": 1, "manager_id": 1},
    )
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
        raise HTTPException(status_code=403, detail="Role Anda tidak memiliki akses Quotations")
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
    raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke quotation ini")


async def find_customer(customer_ref: str):
    ref = str(customer_ref or "").strip()
    if not ref:
        return None
    customer = await db.customers.find_one({"id": ref})
    if customer:
        return customer
    return await db.customers.find_one({"customer_id": ref})


def totals(items):
    subtotal = sum(float(i.quantity) * float(i.unit_price) for i in items)
    discount = sum(float(i.discount or 0) for i in items)
    tax = sum(max(float(i.quantity) * float(i.unit_price) - float(i.discount or 0), 0) * float(i.tax or 0) / 100 for i in items)
    return subtotal, discount, tax, max(subtotal - discount, 0) + tax


@router.get("", response_model=Paginated)
async def list_quotations(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    status: str | None = None,
    sales: str | None = None,
    user: dict = Depends(current_user),
):
    if role_name(user) not in {"SUPER_ADMIN", "SALES_MANAGER", "SALES"}:
        raise HTTPException(status_code=403, detail="Role Anda tidak memiliki akses Quotations")
    visible_ids = await visible_sales_ids(user)
    filters: dict = {"sales_id": {"$in": visible_ids}}
    if status:
        if status not in STATUS_OPTIONS:
            raise HTTPException(status_code=422, detail="Status quotation tidak valid")
        filters["status"] = status
    if sales:
        sales_user = await db.users.find_one({"name": sales, "id": {"$in": visible_ids}}, {"_id": 0, "id": 1})
        if not sales_user:
            raise HTTPException(status_code=403, detail="Sales berada di luar scope Anda")
        filters["sales_id"] = sales_user["id"]
    return await page_collection("quotations", page, page_size, search, filters)


@router.post("", response_model=Quotation)
async def create_quotation(payload: QuotationCreate, user: dict = Depends(current_user)):
    customer = await find_customer(payload.customer_id)
    if not customer:
        raise HTTPException(status_code=400, detail="Customer tidak valid")
    sales_id = payload.sales_id or user.get("id")
    sales = await validate_sales_assignment(str(sales_id), user)
    subtotal, discount, tax, grand = totals(payload.items)
    payload_data = payload.model_dump(mode="json")
    payload_data["customer_id"] = str(customer.get("id") or customer.get("customer_id"))
    payload_data["sales_id"] = str(sales["id"])
    doc = {
        "id": new_id(),
        "number": await next_number("quotations", "QT"),
        "customer_name": customer.get("name") or customer.get("company_name") or "",
        "sales_name": sales["name"],
        "status": "Draft",
        "subtotal": subtotal,
        "discount_total": discount,
        "tax_total": tax,
        "grand_total": grand,
        **payload_data,
        "created_at": now(),
    }
    await db.quotations.insert_one(doc)
    await audit(user, "Create", "Quotations", doc["id"], {"number": doc["number"], "grand_total": grand})
    return Quotation(**doc)


@router.get("/{quotation_id}", response_model=Quotation)
async def get_quotation(quotation_id: str, user: dict = Depends(current_user)):
    doc = await db.quotations.find_one({"id": quotation_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Quotation tidak ditemukan")
    await ensure_access(doc, user)
    doc.pop("_id", None)
    return Quotation(**doc)


@router.put("/{quotation_id}", response_model=Quotation)
async def update_quotation(quotation_id: str, payload: QuotationUpdate, user: dict = Depends(current_user)):
    doc = await db.quotations.find_one({"id": quotation_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Quotation tidak ditemukan")
    await ensure_access(doc, user)
    updates = payload.model_dump(exclude_unset=True, mode="json")
    if "status" in updates and updates["status"] not in STATUS_OPTIONS:
        raise HTTPException(status_code=422, detail="Status quotation tidak valid")
    if "sales_id" in updates:
        if updates["sales_id"]:
            sales = await validate_sales_assignment(str(updates["sales_id"]), user)
            updates["sales_id"] = str(sales["id"])
            updates["sales_name"] = sales["name"]
        else:
            updates["sales_id"] = None
            updates["sales_name"] = None
    if "items" in updates:
        items = updates["items"]
        subtotal = sum(float(i.get("quantity", 0)) * float(i.get("unit_price", 0)) for i in items)
        discount = sum(float(i.get("discount", 0) or 0) for i in items)
        tax = sum(max(float(i.get("quantity", 0)) * float(i.get("unit_price", 0)) - float(i.get("discount", 0) or 0), 0) * float(i.get("tax", 0) or 0) / 100 for i in items)
        updates.update({"subtotal": subtotal, "discount_total": discount, "tax_total": tax, "grand_total": max(subtotal - discount, 0) + tax})
    updates["updated_at"] = now()
    if not updates:
        return Quotation(**doc)
    await db.quotations.update_one({"id": quotation_id}, {"$set": updates})
    await audit(user, "Update", "Quotations", quotation_id, updates)
    fresh = await db.quotations.find_one({"id": quotation_id})
    fresh.pop("_id", None)
    return Quotation(**fresh)


@router.delete("/{quotation_id}")
async def delete_quotation(quotation_id: str, user: dict = Depends(current_user)):
    doc = await db.quotations.find_one({"id": quotation_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Quotation tidak ditemukan")
    await ensure_access(doc, user)
    await db.quotations.delete_one({"id": quotation_id})
    await audit(user, "Delete", "Quotations", quotation_id, {"number": doc.get("number")})
    return {"message": "Quotation dihapus"}


@router.post("/{quotation_id}/duplicate", response_model=Quotation)
async def duplicate_quotation(quotation_id: str, user: dict = Depends(current_user)):
    source = await db.quotations.find_one({"id": quotation_id})
    if not source:
        raise HTTPException(status_code=404, detail="Quotation tidak ditemukan")
    await ensure_access(source, user)
    source.pop("_id", None)
    source["id"] = new_id()
    source["number"] = await next_number("quotations", "QT")
    source["status"] = "Draft"
    source["customer_po_number"] = None
    source["date"] = now().date().isoformat()
    source["created_at"] = now()
    source["updated_at"] = now()
    await db.quotations.insert_one(source)
    await audit(user, "Duplicate", "Quotations", source["id"], {"number": source["number"]})
    return Quotation(**source)


@router.post("/{quotation_id}/customer-po", response_model=Quotation)
async def note_customer_po(quotation_id: str, po_number: str, user: dict = Depends(current_user)):
    po_number = po_number.strip()
    if not po_number:
        raise HTTPException(status_code=422, detail="Nomor PO customer wajib diisi")
    doc = await db.quotations.find_one({"id": quotation_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Quotation tidak ditemukan")
    await ensure_access(doc, user)
    await db.quotations.update_one({"id": quotation_id}, {"$set": {"customer_po_number": po_number, "updated_at": now()}})
    result = await db.quotations.find_one({"id": quotation_id})
    result.pop("_id", None)
    await audit(user, "Customer PO", "Quotations", quotation_id, {"po_number": po_number})
    return Quotation(**result)


@router.get("/{quotation_id}/pdf")
async def quotation_pdf(quotation_id: str, user: dict = Depends(current_user)):
    quotation = await db.quotations.find_one({"id": quotation_id})
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation tidak ditemukan")
    await ensure_access(quotation, user)
    lines = ["CRM SALES MANAGEMENT", f"QUOTATION {quotation['number']}", f"Customer: {quotation['customer_name']}", "", "ITEM | QTY | UNIT PRICE | TOTAL"]
    for item in quotation["items"]:
        lines.append(f"{item['description']} | {item['quantity']} | {item['unit_price']:,.0f} | {item['quantity'] * item['unit_price']:,.0f}")
    lines += ["", f"GRAND TOTAL: Rp {quotation['grand_total']:,.0f}"]
    content = "\\n".join(lines)
    stream = f"BT /F1 11 Tf 50 780 Td ({content.replace('(', '[').replace(')', ']')}) Tj ET".encode()
    pdf = b"%PDF-1.4\n1 0 obj<< /Type /Catalog /Pages 2 0 R>>endobj\n2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1>>endobj\n3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources<< /Font<< /F1 4 0 R>>>> /Contents 5 0 R>>endobj\n4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica>>endobj\n5 0 obj<< /Length " + str(len(stream)).encode() + b">>stream\n" + stream + b"\nendstream endobj\ntrailer<< /Root 1 0 R>>\n%%EOF"
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={quotation['number']}.pdf"})
