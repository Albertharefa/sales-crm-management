from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from lib.db import db
from models.customer import (
    Customer,
    CustomerCreate,
    Contact,
    ContactCreate,
    Paginated,
)
from routers.common import audit, new_id, now
from routers.deps import current_user


router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


# ============================================================
# HELPER
# ============================================================

async def visible_filter(
    user: dict,
    owner_id_field: str = "sales_id",
    owner_name_field: str = "sales_name",
) -> dict:
    """
    Menentukan data customer yang boleh dilihat user.
    """

    # SUPER ADMIN dapat melihat semua data
    if user.get("role") == "SUPER_ADMIN":
        return {}

    # SALES MANAGER dapat melihat dirinya + sales di bawahnya
    if user.get("role") == "SALES_MANAGER":
        reports = await db.users.find(
            {"manager_id": user["id"]},
            {"_id": 0, "id": 1, "name": 1},
        ).to_list(100)

        ids = [
            user["id"],
            *[item["id"] for item in reports],
        ]

        names = [
            user["name"],
            *[item["name"] for item in reports],
        ]

        return {
            "$or": [
                {owner_id_field: {"$in": ids}},
                {owner_name_field: {"$in": names}},
            ]
        }

    # SALES biasa hanya melihat customer miliknya
    return {
        "$or": [
            {owner_id_field: user["id"]},
            {owner_name_field: user["name"]},
        ]
    }


async def get_customer_by_id(
    customer_id: str,
    user: dict,
) -> dict:
    """
    Mengambil customer berdasarkan customer_id
    dengan pengecekan hak akses.
    """

    visibility = await visible_filter(user)

    query = {
        "customer_id": customer_id,
    }

    if visibility:
        query.update(visibility)

    customer = await db.customers.find_one(
        query,
        {"_id": 0},
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan atau tidak dapat diakses",
        )

    return customer


async def generate_customer_id() -> str:
    """
    Generate customer ID:
    CUS-2026-00001
    CUS-2026-00002
    dst.
    """

    year = now().year
    prefix = f"CUS-{year}-"

    last_customer = await db.customers.find_one(
        {
            "customer_id": {
                "$regex": f"^{prefix}"
            }
        },
        sort=[
            ("customer_id", -1)
        ],
    )

    if not last_customer:
        return f"{prefix}00001"

    last_id = last_customer.get("customer_id", "")

    try:
        last_number = int(last_id.split("-")[-1])
    except (ValueError, IndexError):
        last_number = 0

    return f"{prefix}{last_number + 1:05d}"


async def generate_contact_id() -> str:
    """
    Generate contact ID:
    CON-2026-00001
    CON-2026-00002
    dst.
    """

    year = now().year
    prefix = f"CON-{year}-"

    last_contact = await db.contacts.find_one(
        {
            "contact_id": {
                "$regex": f"^{prefix}"
            }
        },
        sort=[
            ("contact_id", -1)
        ],
    )

    if not last_contact:
        return f"{prefix}00001"

    last_id = last_contact.get("contact_id", "")

    try:
        last_number = int(last_id.split("-")[-1])
    except (ValueError, IndexError):
        last_number = 0

    return f"{prefix}{last_number + 1:05d}"


# ============================================================
# GET /customers
# LIST CUSTOMERS
# ============================================================

@router.get(
    "",
    response_model=Paginated,
)
async def list_customers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    industry: Optional[str] = None,
    sales_id: Optional[str] = None,
    user: dict = Depends(current_user),
):
    visibility = await visible_filter(user)

    query: dict[str, Any] = {}

    if visibility:
        query.update(visibility)

    # Search
    if search:
        search_regex = {
            "$regex": search,
            "$options": "i",
        }

        query["$or"] = [
            {"name": search_regex},
            {"company": search_regex},
            {"pic_name": search_regex},
            {"email": search_regex},
            {"customer_id": search_regex},
        ]

    # Filter status
    if status:
        query["status"] = status

    # Filter industry
    if industry:
        query["industry"] = industry

    # Filter sales
    if sales_id:
        query["sales_id"] = sales_id

    total = await db.customers.count_documents(query)

    skip = (page - 1) * page_size

    items = await db.customers.find(
        query,
        {"_id": 0},
    ).sort(
        "created_at",
        -1,
    ).skip(
        skip
    ).limit(
        page_size
    ).to_list(page_size)

    return Paginated(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


# ============================================================
# POST /customers
# CREATE CUSTOMER
# ============================================================

@router.post(
    "",
    response_model=Customer,
)
async def create_customer(
    payload: CustomerCreate,
    user: dict = Depends(current_user),
):
    # Jika sales_id tidak dikirim, gunakan user yang sedang login
    sales_id = payload.sales_id or user.get("id")
    sales_name = user.get("name")

    # Jika sales_id diberikan, ambil nama sales
    if payload.sales_id:
        sales_user = await db.users.find_one(
            {"id": payload.sales_id},
            {"_id": 0, "id": 1, "name": 1},
        )

        if sales_user:
            sales_name = sales_user.get("name")

    customer_id = await generate_customer_id()

    created_at = now()

    customer = {
        "id": new_id(),
        "customer_id": customer_id,
        "name": payload.name,
        "company": getattr(payload, "company", None),
        "industry": payload.industry,
        "city": payload.city,
        "province": payload.province,
        "phone": payload.phone,
        "email": payload.email,
        "pic_name": payload.pic_name,
        "pic_position": payload.pic_position,
        "source": payload.source,
        "status": payload.status,
        "sales_id": sales_id,
        "sales_name": sales_name,
        "address": payload.address,
        "notes": payload.notes,
        "created_at": created_at,
        "updated_at": created_at,
    }

    await db.customers.insert_one(customer)

    await audit(
        user,
        "Create",
        "Customers",
        customer["id"],
        {
            "customer_id": customer_id,
            "name": payload.name,
        },
    )

    return Customer(**customer)


# ============================================================
# GET /customers/{customer_id}
# GET CUSTOMER
# ============================================================

@router.get(
    "/{customer_id}",
    response_model=Customer,
)
async def get_customer(
    customer_id: str,
    user: dict = Depends(current_user),
):
    customer = await get_customer_by_id(
        customer_id,
        user,
    )

    return Customer(**customer)


# ============================================================
# PUT /customers/{customer_id}
# UPDATE CUSTOMER
# ============================================================

@router.put(
    "/{customer_id}",
    response_model=Customer,
)
async def update_customer(
    customer_id: str,
    payload: CustomerCreate,
    user: dict = Depends(current_user),
):
    existing = await get_customer_by_id(
        customer_id,
        user,
    )

    sales_id = payload.sales_id or existing.get("sales_id")
    sales_name = existing.get("sales_name")

    if payload.sales_id:
        sales_user = await db.users.find_one(
            {"id": payload.sales_id},
            {"_id": 0, "id": 1, "name": 1},
        )

        if sales_user:
            sales_name = sales_user.get("name")

    update_data = {
        "name": payload.name,
        "industry": payload.industry,
        "city": payload.city,
        "province": payload.province,
        "phone": payload.phone,
        "email": payload.email,
        "pic_name": payload.pic_name,
        "pic_position": payload.pic_position,
        "source": payload.source,
        "status": payload.status,
        "sales_id": sales_id,
        "sales_name": sales_name,
        "address": payload.address,
        "notes": payload.notes,
        "updated_at": now(),
    }

    # Hanya update company bila field tersebut tersedia
    if hasattr(payload, "company"):
        update_data["company"] = getattr(
            payload,
            "company",
            None,
        )

    await db.customers.update_one(
        {
            "customer_id": customer_id,
        },
        {
            "$set": update_data,
        },
    )

    updated = await db.customers.find_one(
        {
            "customer_id": customer_id,
        },
        {
            "_id": 0,
        },
    )

    await audit(
        user,
        "Update",
        "Customers",
        existing["id"],
        {
            "customer_id": customer_id,
            "changes": update_data,
        },
    )

    return Customer(**updated)


# ============================================================
# DELETE /customers/{customer_id}
# DELETE CUSTOMER
# ============================================================

@router.delete(
    "/{customer_id}",
    status_code=204,
)
async def delete_customer(
    customer_id: str,
    user: dict = Depends(current_user),
):
    existing = await get_customer_by_id(
        customer_id,
        user,
    )

    await db.customers.delete_one(
        {
            "customer_id": customer_id,
        }
    )

    await audit(
        user,
        "Delete",
        "Customers",
        existing["id"],
        {
            "customer_id": customer_id,
            "name": existing.get("name"),
        },
    )

    return None


# ============================================================
# GET /customers/{customer_id}/contacts
# LIST CUSTOMER CONTACTS
# ============================================================

@router.get(
    "/{customer_id}/contacts",
    response_model=list[Contact],
)
async def list_customer_contacts(
    customer_id: str,
    user: dict = Depends(current_user),
):
    customer = await get_customer_by_id(
        customer_id,
        user,
    )

    contacts = await db.contacts.find(
        {
            "customer_id": customer_id,
        },
        {
            "_id": 0,
        },
    ).sort(
        "created_at",
        -1,
    ).to_list(500)

    return [
        Contact(**contact)
        for contact in contacts
    ]


# ============================================================
# POST /customers/{customer_id}/contacts
# CREATE CUSTOMER CONTACT
# ============================================================

@router.post(
    "/{customer_id}/contacts",
    response_model=Contact,
    status_code=201,
)
async def create_customer_contact(
    customer_id: str,
    payload: ContactCreate,
    user: dict = Depends(current_user),
):
    # Pastikan customer ada dan user punya akses
    customer = await get_customer_by_id(
        customer_id,
        user,
    )

    contact_id = await generate_contact_id()

    created_at = now()

    contact = {
        "id": new_id(),
        "contact_id": contact_id,
        "customer_id": customer_id,
        "customer_name": customer.get(
            "name",
            "",
        ),
        "first_name": payload.first_name,
        "last_name": payload.last_name,
        "position": payload.position,
        "department": payload.department,
        "email": payload.email,
        "mobile": payload.mobile,
        "contact_type": payload.contact_type,
        "is_decision_maker": payload.is_decision_maker,
        "status": payload.status,
        "notes": payload.notes,
        "created_at": created_at,
    }

    await db.contacts.insert_one(
        contact
    )

    await audit(
        user,
        "Create",
        "Customer Contacts",
        contact["id"],
        {
            "contact_id": contact_id,
            "customer_id": customer_id,
            "customer_name": customer.get("name"),
            "contact_name": (
                f"{payload.first_name} "
                f"{payload.last_name or ''}"
            ).strip(),
        },
    )

    return Contact(**contact)
