from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from lib.db import db
from models.crm import Paginated, Quotation, QuotationCreate
from routers.common import audit, new_id, next_number, now, page_collection
from routers.deps import current_user

router = APIRouter(prefix="/quotations", tags=["quotations"])


def totals(items):
    subtotal = sum(i.quantity * i.unit_price for i in items)
    discount = sum(i.discount for i in items)
    taxable = max(subtotal - discount, 0)
    tax = sum(max(i.quantity * i.unit_price - i.discount, 0) * i.tax / 100 for i in items)
    return subtotal, discount, tax, taxable + tax


@router.get("", response_model=Paginated)
async def list_quotations(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", status: str | None = None, sales: str | None = None, user: dict = Depends(current_user)):
    filters = {}
    if status:
        filters["status"] = status
    if sales:
        filters["sales_name"] = sales
    return await page_collection("quotations", page, page_size, search, filters)


@router.post("", response_model=Quotation)
async def create_quotation(payload: QuotationCreate, user: dict = Depends(current_user)):
    customer = await db.customers.find_one({"id": payload.customer_id})
    if not customer:
        raise HTTPException(status_code=400, detail="Customer tidak valid")
    subtotal, discount, tax, grand = totals(payload.items)
    doc = {"id": new_id(), "number": await next_number("quotations", "QT"), "customer_name": customer["name"], "sales_name": user["name"], "status": "Draft", "subtotal": subtotal, "discount_total": discount, "tax_total": tax, "grand_total": grand, **payload.model_dump(mode="json"), "created_at": now()}
    await db.quotations.insert_one(doc)
    await audit(user, "Create", "Quotations", doc["id"], {"number": doc["number"], "grand_total": grand})
    return Quotation(**doc)


@router.get("/{quotation_id}/pdf")
async def quotation_pdf(quotation_id: str, user: dict = Depends(current_user)):
    quotation = await db.quotations.find_one({"id": quotation_id})
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation tidak ditemukan")
    lines = ["CRM SALES MANAGEMENT", f"QUOTATION {quotation['number']}", f"Customer: {quotation['customer_name']}", "", "ITEM | QTY | UNIT PRICE | TOTAL"]
    for item in quotation["items"]:
        lines.append(f"{item['description']} | {item['quantity']} | {item['unit_price']:,.0f} | {item['quantity'] * item['unit_price']:,.0f}")
    lines += ["", f"GRAND TOTAL: Rp {quotation['grand_total']:,.0f}"]
    content = "\\n".join(lines)
    stream = f"BT /F1 11 Tf 50 780 Td ({content.replace('(', '[').replace(')', ']')}) Tj ET".encode()
    pdf = b"%PDF-1.4\n1 0 obj<< /Type /Catalog /Pages 2 0 R>>endobj\n2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1>>endobj\n3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources<< /Font<< /F1 4 0 R>>>> /Contents 5 0 R>>endobj\n4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica>>endobj\n5 0 obj<< /Length " + str(len(stream)).encode() + b">>stream\n" + stream + b"\nendstream endobj\ntrailer<< /Root 1 0 R>>\n%%EOF"
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={quotation['number']}.pdf"})