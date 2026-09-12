from fastapi import APIRouter, Depends, HTTPException, Query
from lib.db import db
from models.crm import Product, ProductCreate, Paginated
from routers.common import audit, new_id, now, page_collection
from routers.deps import current_user, require_roles

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=Paginated)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    category: str | None = None,
    user: dict = Depends(current_user),
):
    return await page_collection(
        "products",
        page,
        page_size,
        search,
        {"category": category} if category else {},
    )


@router.post("", response_model=Product)
async def create_product(
    payload: ProductCreate,
    user: dict = Depends(require_roles("SUPER_ADMIN")),
):
    if await db.products.find_one({"code": payload.code}):
        raise HTTPException(status_code=409, detail="Kode produk sudah digunakan")
    doc = {"id": new_id(), **payload.model_dump(), "created_at": now()}
    await db.products.insert_one(doc)
    await audit(user, "Create", "Products", doc["id"], {"code": doc["code"]})
    return Product(**doc)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    user: dict = Depends(require_roles("SUPER_ADMIN")),
):
    product = await db.products.find_one({"id": product_id}, {"_id": 0, "id": 1, "code": 1, "name": 1})
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    quotation_ref = await db.quotations.find_one({"items.product_id": product_id}, {"_id": 1})
    order_ref = await db.purchase_orders.find_one({"items.product_id": product_id}, {"_id": 1})
    if quotation_ref or order_ref:
        raise HTTPException(status_code=409, detail="Produk sudah digunakan pada quotation atau Purchase Order dan tidak dapat dihapus")
    result = await db.products.delete_one({"id": product_id})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    await audit(user, "Delete", "Products", product_id)
