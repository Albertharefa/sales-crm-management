from fastapi import APIRouter, Depends, HTTPException, Query
from lib.db import db
from models.crm import Customer, CustomerCreate, Paginated, Contact
from routers.common import audit, new_id, now
from routers.deps import current_user

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=Paginated)
async def list_customers(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", status: str | None = None, industry: str | None = None, user: dict = Depends(current_user)):
    query = {key: value for key, value in {"status": status, "industry": industry}.items() if value}
    from routers.common import page_collection
    return await page_collection("customers", page, page_size, search, query)


@router.post("", response_model=Customer)
async def create_customer(payload: CustomerCreate, user: dict = Depends(current_user)):
    duplicate = await db.customers.find_one({"name": {"$regex": f"^{payload.name}$", "$options": "i"}})
    if duplicate:
        raise HTTPException(status_code=409, detail="Customer dengan nama tersebut sudah ada")
    count = await db.customers.count_documents({}) + 1
    doc = {"id": new_id(), "customer_id": f"CUS-{now().year}-{count:05d}", **payload.model_dump(mode="json"), "sales_name": user.get("name"), "created_at": now(), "updated_at": now()}
    await db.customers.insert_one(doc)
    await audit(user, "Create", "Customers", doc["id"], {"name": doc["name"]})
    return Customer(**doc)


@router.get("/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str, user: dict = Depends(current_user)):
    doc = await db.customers.find_one({"id": customer_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    return Customer(**doc)


@router.put("/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, payload: CustomerCreate, user: dict = Depends(current_user)):
    doc = await db.customers.find_one({"id": customer_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    update = {**payload.model_dump(mode="json"), "updated_at": now()}
    await db.customers.update_one({"id": customer_id}, {"$set": update})
    await audit(user, "Update", "Customers", customer_id, update)
    return Customer(**{**doc, **update})


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(customer_id: str, user: dict = Depends(current_user)):
    result = await db.customers.delete_one({"id": customer_id})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    await audit(user, "Delete", "Customers", customer_id)


@router.get("/{customer_id}/contacts", response_model=list[Contact])
async def customer_contacts(customer_id: str, user: dict = Depends(current_user)):
    docs = await db.contacts.find({"customer_id": customer_id}).sort("created_at", -1).to_list(1000)
    return [Contact(**doc) for doc in docs]