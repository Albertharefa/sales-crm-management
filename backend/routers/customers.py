from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import csv
import io
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict

from lib.db import db
from routers.deps import current_user
from services.sales import get_sales_options


router = APIRouter(
    prefix="/customers",
    tags=["customers"],
    dependencies=[Depends(current_user)],
)


INACTIVE_STATUSES = {"INACTIVE", "DISABLED"}
VALID_ROLES = {"SUPER_ADMIN", "SALES_MANAGER", "SALES"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def role_name(user: dict) -> str:
    return str(user.get("role") or "").strip().upper()


def _clean(value: Any) -> str:
    return str(value or "").strip()


async def visible_sales(user: dict) -> list[dict[str, Any]]:
    """Return active Sales users visible to the current role."""
    role = role_name(user)
    if role == "SUPER_ADMIN":
        query = {
            "role": "SALES",
            "status": {"$nin": list(INACTIVE_STATUSES)},
        }
    elif role == "SALES_MANAGER":
        query = {
            "manager_id": user.get("id"),
            "role": "SALES",
            "status": {"$nin": list(INACTIVE_STATUSES)},
        }
    elif role == "SALES":
        query = {"id": user.get("id"), "role": "SALES"}
    else:
        return []

    return await db.users.find(
        query,
        {"_id": 0, "id": 1, "name": 1, "role": 1, "status": 1, "manager_id": 1},
    ).sort("name", 1).to_list(1000)


async def visible_sales_ids(user: dict) -> list[str]:
    users = await visible_sales(user)
    return [_clean(item.get("id")) for item in users if _clean(item.get("id"))]


async def visible_sales_names(user: dict) -> list[str]:
    users = await visible_sales(user)
    return [_clean(item.get("name")) for item in users if _clean(item.get("name"))]


async def customer_scope_query(user: dict) -> dict[str, Any]:
    """Mongo filter enforcing customer ownership/team visibility."""
    if role_name(user) == "SUPER_ADMIN":
        return {}

    ids = await visible_sales_ids(user)
    names = await visible_sales_names(user)
    if not ids and not names:
        return {"_id": {"$exists": False}}

    # Support canonical sales_id plus legacy sales_name-only records.
    return {
        "$or": [
            {"sales_id": {"$in": ids}},
            {"sales_name": {"$in": names}},
        ]
    }


async def ensure_customer_access(customer: dict, user: dict) -> None:
    if role_name(user) == "SUPER_ADMIN":
        return

    sales_id = _clean(customer.get("sales_id"))
    sales_name = _clean(customer.get("sales_name"))
    ids = await visible_sales_ids(user)
    names = await visible_sales_names(user)
    if sales_id in ids or sales_name in names:
        return
    raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke customer ini")


async def validate_sales_assignment(sales_id: str | None, user: dict) -> dict:
    role = role_name(user)
    selected = _clean(sales_id)
    if not selected:
        if role == "SALES":
            selected = _clean(user.get("id"))
        else:
            raise HTTPException(status_code=422, detail="Sales customer wajib dipilih")

    sales = await db.users.find_one(
        {"id": selected, "role": "SALES"},
        {"_id": 0, "id": 1, "name": 1, "role": 1, "status": 1, "manager_id": 1},
    )
    if not sales:
        raise HTTPException(status_code=400, detail="Sales customer tidak valid")

    if _clean(sales.get("status")).upper() in INACTIVE_STATUSES:
        raise HTTPException(status_code=400, detail="Sales customer tidak aktif")

    if role == "SALES" and _clean(sales.get("id")) != _clean(user.get("id")):
        raise HTTPException(status_code=403, detail="Sales hanya dapat menggunakan akun sendiri")

    if role == "SALES_MANAGER" and _clean(sales.get("manager_id")) != _clean(user.get("id")):
        raise HTTPException(status_code=403, detail="Sales tersebut bukan anggota team Anda")

    if role not in VALID_ROLES:
        raise HTTPException(status_code=403, detail="Role Anda tidak memiliki akses Customers")

    return sales


# ============================================================
# CUSTOMER RESPONSE MODELS
# ============================================================

class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    customer_id: str
    name: str = ""
    company_name: str = ""
    company: Optional[str] = None
    industry: str = "Manufacturing"
    source: str = "Referral"
    city: str = "Jakarta"
    province: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    pic_name: Optional[str] = None
    pic_position: Optional[str] = None
    status: str = "Active"
    sales_id: Optional[str] = None
    sales_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginatedCustomers(BaseModel):
    items: List[Customer]
    page: int
    page_size: int
    total: int


class CustomerCreate(BaseModel):
    name: str = ""
    company_name: Optional[str] = None
    company: Optional[str] = None
    industry: str = "Manufacturing"
    source: str = "Referral"
    city: str = "Jakarta"
    province: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    pic_name: Optional[str] = None
    pic_position: Optional[str] = None
    status: str = "Active"
    sales_id: Optional[str] = None
    sales_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    source: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    pic_name: Optional[str] = None
    pic_position: Optional[str] = None
    status: Optional[str] = None
    sales_id: Optional[str] = None
    sales_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# NORMALIZATION / LOOKUP
# ============================================================

def normalize_customer(data: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(data)
    company_name = item.get("company_name") or item.get("company") or ""
    item["company_name"] = company_name
    item.setdefault("company", company_name)
    item.setdefault("id", "")
    item.setdefault("customer_id", "")
    item.setdefault("name", "")
    item.setdefault("industry", "Manufacturing")
    item.setdefault("city", "Jakarta")
    item.setdefault("province", "")
    item.setdefault("phone", "")
    item.setdefault("email", "")
    item.setdefault("pic_name", "")
    item.setdefault("pic_position", "")
    item.setdefault("status", "Active")
    item.setdefault("sales_id", None)
    item.setdefault("sales_name", "")
    item.setdefault("address", "")
    item.setdefault("notes", "")
    return item


async def find_customer(customer_id: str):
    ref = _clean(customer_id)
    if not ref:
        return None
    return (
        await db.customers.find_one({"customer_id": ref}, {"_id": 0})
        or await db.customers.find_one({"id": ref}, {"_id": 0})
        or await db.customers.find_one(
            {"customer_id": {"$regex": f"^{re.escape(ref)}$", "$options": "i"}},
            {"_id": 0},
        )
    )


async def generate_customer_id() -> str:
    year = utc_now().year
    prefix = f"CUS-{year}-"
    last_customer = await db.customers.find_one(
        {"customer_id": {"$regex": f"^{re.escape(prefix)}"}},
        sort=[("customer_id", -1)],
    )
    if not last_customer:
        return f"{prefix}00001"
    try:
        number = int(str(last_customer.get("customer_id", "")).split("-")[-1]) + 1
    except Exception:
        number = 1
    return f"{prefix}{number:05d}"


# ============================================================
# EXPORT
# ============================================================

@router.get("/export", summary="Export Customers CSV")
async def export_customers(user: dict = Depends(current_user)):
    columns = [
        "created_at", "customer_id", "company_name", "name PIC", "phone",
        "pic_position", "address", "city", "province", "email", "industry",
        "notes", "Sales_Name", "sales_id", "source", "status",
    ]
    scope = await customer_scope_query(user)
    cursor = db.customers.find(scope, {"_id": 0}).sort("created_at", -1)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(columns)
    async for raw in cursor:
        customer = normalize_customer(raw)
        created_at = customer.get("created_at")
        if isinstance(created_at, datetime):
            created_at_value = f"{created_at.month}/{created_at.day}/{created_at.year}"
        elif created_at:
            try:
                parsed = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
                created_at_value = f"{parsed.month}/{parsed.day}/{parsed.year}"
            except ValueError:
                created_at_value = str(created_at)
        else:
            created_at_value = ""
        writer.writerow([
            created_at_value, customer.get("customer_id", ""), customer.get("company_name", ""),
            customer.get("pic_name", ""), customer.get("phone", ""), customer.get("pic_position", ""),
            customer.get("address", ""), customer.get("city", ""), customer.get("province", ""),
            customer.get("email", ""), customer.get("industry", ""), customer.get("notes", ""),
            customer.get("sales_name", ""), customer.get("sales_id", ""), customer.get("source", ""),
            customer.get("status", ""),
        ])
    return StreamingResponse(
        iter(["\ufeff" + buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="customers.csv"'},
    )


# ============================================================
# LIST
# ============================================================

@router.get("", response_model=PaginatedCustomers, summary="List Customers")
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = Query(""),
    status: str = Query(""),
    industry: str = Query(""),
    sales_id: str = Query(""),
    sales_name: str = Query(""),
    user: dict = Depends(current_user),
):
    try:
        scope = await customer_scope_query(user)
        filters: Dict[str, Any] = {"$and": [scope]} if scope else {}

        if search.strip():
            term = re.escape(search.strip())
            filters.setdefault("$and", []).append({
                "$or": [
                    {"name": {"$regex": term, "$options": "i"}},
                    {"company_name": {"$regex": term, "$options": "i"}},
                    {"company": {"$regex": term, "$options": "i"}},
                    {"customer_id": {"$regex": term, "$options": "i"}},
                    {"pic_name": {"$regex": term, "$options": "i"}},
                    {"email": {"$regex": term, "$options": "i"}},
                ]
            })

        if status.strip() and status.strip().lower() != "semua status":
            filters["status"] = status.strip()
        if industry.strip() and industry.strip().lower() != "semua industri":
            filters["industry"] = industry.strip()

        if sales_id.strip():
            selected = sales_id.strip()
            allowed = await visible_sales_ids(user)
            if role_name(user) != "SUPER_ADMIN" and selected not in allowed:
                raise HTTPException(status_code=403, detail="Sales berada di luar scope Anda")
            sales_user = await db.users.find_one({"id": selected, "role": "SALES"}, {"_id": 0, "id": 1, "name": 1})
            if not sales_user:
                raise HTTPException(status_code=400, detail="Sales tidak valid")
            filters["$or"] = [{"sales_id": selected}, {"sales_name": sales_user.get("name", "")}]
        elif sales_name.strip() and sales_name.strip().lower() != "semua sales":
            allowed_names = await visible_sales_names(user)
            if role_name(user) != "SUPER_ADMIN" and sales_name.strip() not in allowed_names:
                raise HTTPException(status_code=403, detail="Sales berada di luar scope Anda")
            filters["sales_name"] = sales_name.strip()

        # Keep search and scope combined even when a Sales filter is selected.
        if "$or" in filters and "$and" in filters:
            sales_filter = filters.pop("$or")
            filters["$and"].append({"$or": sales_filter})

        total = await db.customers.count_documents(filters)
        customers = await db.customers.find(filters, {"_id": 0}).sort(
            [("created_at", -1), ("customer_id", -1)]
        ).skip((page - 1) * page_size).limit(page_size).to_list(page_size)
        items = [Customer.model_validate(normalize_customer(item)) for item in customers]
        return PaginatedCustomers(items=items, page=page, page_size=page_size, total=total)
    except HTTPException:
        raise
    except Exception as exc:
        print(f"ERROR: GET /customers failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to list customers: {str(exc)}")


# ============================================================
# SALES OPTIONS
# ============================================================

@router.get("/sales-options", summary="List Sales from Shared Sales Master")
async def customer_sales_options(user: dict = Depends(current_user)):
    allowed_ids = set(await visible_sales_ids(user))
    options = await get_sales_options()
    if role_name(user) == "SUPER_ADMIN":
        return options
    return [item for item in options if _clean(item.get("id")) in allowed_ids]


# ============================================================
# GET
# ============================================================

@router.get("/{customer_id}", response_model=Customer, summary="Get Customer")
async def get_customer(customer_id: str, user: dict = Depends(current_user)):
    try:
        customer = await find_customer(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found.")
        await ensure_customer_access(customer, user)
        return Customer.model_validate(normalize_customer(customer))
    except HTTPException:
        raise
    except Exception as exc:
        print(f"ERROR: GET /customers/{customer_id} failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to get customer: {str(exc)}")


# ============================================================
# CREATE
# ============================================================

@router.post("", response_model=Customer, summary="Create Customer")
async def create_customer(payload: CustomerCreate, user: dict = Depends(current_user)):
    try:
        sales = await validate_sales_assignment(payload.sales_id, user)
        created = utc_now()
        customer_id = await generate_customer_id()
        company_name = payload.company_name or payload.company or ""
        customer = {
            "id": customer_id,
            "customer_id": customer_id,
            "name": payload.name,
            "company_name": company_name,
            "company": company_name,
            "industry": payload.industry,
            "source": payload.source,
            "city": payload.city,
            "province": payload.province,
            "phone": payload.phone,
            "email": payload.email,
            "pic_name": payload.pic_name,
            "pic_position": payload.pic_position,
            "status": payload.status,
            "sales_id": sales["id"],
            "sales_name": sales["name"],
            "address": payload.address,
            "notes": payload.notes,
            "created_at": created,
            "updated_at": created,
        }
        await db.customers.insert_one(customer)
        return Customer.model_validate(normalize_customer(customer))
    except HTTPException:
        raise
    except Exception as exc:
        print(f"ERROR: POST /customers failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to create customer: {str(exc)}")


# ============================================================
# UPDATE
# ============================================================

@router.put("/{customer_id}", response_model=Customer, summary="Update Customer")
async def update_customer(customer_id: str, payload: CustomerUpdate, user: dict = Depends(current_user)):
    try:
        existing = await find_customer(customer_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found.")
        await ensure_customer_access(existing, user)

        update_data = payload.model_dump(exclude_unset=True)
        if "sales_id" in update_data:
            sales = await validate_sales_assignment(update_data.get("sales_id"), user)
            update_data["sales_id"] = sales["id"]
            update_data["sales_name"] = sales["name"]
        elif "sales_name" in update_data and update_data.get("sales_name"):
            names = await visible_sales_names(user)
            if role_name(user) != "SUPER_ADMIN" and update_data["sales_name"] not in names:
                raise HTTPException(status_code=403, detail="Sales berada di luar scope Anda")

        if "company_name" in update_data and update_data["company_name"] is not None:
            update_data["company"] = update_data["company_name"]
        elif "company" in update_data and update_data["company"] is not None:
            update_data["company_name"] = update_data["company"]

        update_data["updated_at"] = utc_now()
        await db.customers.update_one({"id": existing.get("id")}, {"$set": update_data})
        updated = await db.customers.find_one({"id": existing.get("id")}, {"_id": 0})
        return Customer.model_validate(normalize_customer(updated))
    except HTTPException:
        raise
    except Exception as exc:
        print(f"ERROR: PUT /customers/{customer_id} failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to update customer: {str(exc)}")


# ============================================================
# DELETE
# ============================================================

@router.delete("/{customer_id}", summary="Delete Customer")
async def delete_customer(customer_id: str, user: dict = Depends(current_user)):
    try:
        existing = await find_customer(customer_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found.")
        await ensure_customer_access(existing, user)
        await db.customers.delete_one({"id": existing.get("id")})
        return {"status": "success", "message": "Customer deleted successfully", "customer_id": customer_id}
    except HTTPException:
        raise
    except Exception as exc:
        print(f"ERROR: DELETE /customers/{customer_id} failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to delete customer: {str(exc)}")
