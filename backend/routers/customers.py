from fastapi import APIRouter, Depends, HTTPException, Query

from lib.db import db
from models.crm import Customer, CustomerCreate, Paginated, Contact
from routers.common import audit, new_id, now
from routers.deps import current_user


router = APIRouter(
    prefix="/customers",
    tags=["customers"]
)


# ============================================================
# HELPER
# ============================================================

async def find_customer(customer_id: str):
    """
    Mencari customer berdasarkan:
    1. customer_id CRM, contoh: CUS-2026-00001
    2. id internal UUID
    """

    doc = await db.customers.find_one(
        {
            "$or": [
                {"customer_id": customer_id},
                {"id": customer_id}
            ]
        }
    )

    return doc


# ============================================================
# GET /customers
# LIST CUSTOMERS
# ============================================================

@router.get(
    "",
    response_model=Paginated
)
async def list_customers(
    page: int = Query(
        1,
        ge=1
    ),
    page_size: int = Query(
        25,
        ge=1,
        le=100
    ),
    search: str = "",
    status: str | None = None,
    industry: str | None = None,
    user: dict = Depends(current_user)
):
    """
    Menampilkan daftar customer dengan pagination,
    search, status dan industry filter.
    """

    query = {
        key: value
        for key, value in {
            "status": status,
            "industry": industry
        }.items()
        if value
    }

    from routers.common import page_collection

    return await page_collection(
        "customers",
        page,
        page_size,
        search,
        query
    )


# ============================================================
# POST /customers
# CREATE CUSTOMER
# ============================================================

@router.post(
    "",
    response_model=Customer
)
async def create_customer(
    payload: CustomerCreate,
    user: dict = Depends(current_user)
):
    """
    Membuat customer baru.
    """

    # --------------------------------------------------------
    # CEK DUPLIKAT NAMA CUSTOMER
    # --------------------------------------------------------

    duplicate = await db.customers.find_one(
        {
            "name": {
                "$regex": f"^{payload.name}$",
                "$options": "i"
            }
        }
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Customer dengan nama tersebut sudah ada"
        )

    # --------------------------------------------------------
    # GENERATE CUSTOMER ID
    # --------------------------------------------------------

    count = await db.customers.count_documents({}) + 1

    customer_id = f"CUS-{now().year}-{count:05d}"

    # --------------------------------------------------------
    # CREATE DOCUMENT
    # --------------------------------------------------------

    current_time = now()

    doc = {
        "id": new_id(),

        "customer_id": customer_id,

        **payload.model_dump(mode="json"),

        "sales_name": user.get("name"),

        "created_at": current_time,

        "updated_at": current_time
    }

    # --------------------------------------------------------
    # SAVE TO DATABASE
    # --------------------------------------------------------

    await db.customers.insert_one(doc)

    # --------------------------------------------------------
    # AUDIT LOG
    # --------------------------------------------------------

    await audit(
        user,
        "Create",
        "Customers",
        doc["id"],
        {
            "name": doc["name"],
            "customer_id": doc["customer_id"]
        }
    )

    return Customer(**doc)


# ============================================================
# GET /customers/{customer_id}
# GET CUSTOMER DETAIL
# ============================================================

@router.get(
    "/{customer_id}",
    response_model=Customer
)
async def get_customer(
    customer_id: str,
    user: dict = Depends(current_user)
):
    """
    Mengambil detail customer.

    Bisa menggunakan:
    CUS-2026-00001

    atau internal UUID.
    """

    doc = await find_customer(customer_id)

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan"
        )

    return Customer(**doc)


# ============================================================
# PUT /customers/{customer_id}
# UPDATE CUSTOMER
# ============================================================

@router.put(
    "/{customer_id}",
    response_model=Customer
)
async def update_customer(
    customer_id: str,
    payload: CustomerCreate,
    user: dict = Depends(current_user)
):
    """
    Update customer berdasarkan customer_id CRM
    atau internal UUID.
    """

    # --------------------------------------------------------
    # FIND CUSTOMER
    # --------------------------------------------------------

    doc = await find_customer(customer_id)

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan"
        )

    # --------------------------------------------------------
    # CEK DUPLIKAT NAMA
    # --------------------------------------------------------

    duplicate = await db.customers.find_one(
        {
            "name": {
                "$regex": f"^{payload.name}$",
                "$options": "i"
            },
            "id": {
                "$ne": doc["id"]
            }
        }
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Customer dengan nama tersebut sudah ada"
        )

    # --------------------------------------------------------
    # UPDATE DATA
    # --------------------------------------------------------

    update = {
        **payload.model_dump(mode="json"),
        "updated_at": now()
    }

    await db.customers.update_one(
        {
            "id": doc["id"]
        },
        {
            "$set": update
        }
    )

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    await audit(
        user,
        "Update",
        "Customers",
        doc["id"],
        update
    )

    # --------------------------------------------------------
    # RETURN UPDATED CUSTOMER
    # --------------------------------------------------------

    return Customer(
        **{
            **doc,
            **update
        }
    )


# ============================================================
# DELETE /customers/{customer_id}
# DELETE CUSTOMER
# ============================================================

@router.delete(
    "/{customer_id}",
    status_code=204
)
async def delete_customer(
    customer_id: str,
    user: dict = Depends(current_user)
):
    """
    Delete customer berdasarkan customer_id CRM
    atau internal UUID.
    """

    # --------------------------------------------------------
    # FIND CUSTOMER
    # --------------------------------------------------------

    doc = await find_customer(customer_id)

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan"
        )

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    result = await db.customers.delete_one(
        {
            "id": doc["id"]
        }
    )

    if not result.deleted_count:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan"
        )

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    await audit(
        user,
        "Delete",
        "Customers",
        doc["id"]
    )


# ============================================================
# GET /customers/{customer_id}/contacts
# CUSTOMER CONTACTS
# ============================================================

@router.get(
    "/{customer_id}/contacts",
    response_model=list[Contact]
)
async def customer_contacts(
    customer_id: str,
    user: dict = Depends(current_user)
):
    """
    Menampilkan semua contact milik customer.
    """

    # --------------------------------------------------------
    # FIND CUSTOMER
    # --------------------------------------------------------

    customer = await find_customer(customer_id)

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan"
        )

    # --------------------------------------------------------
    # GUNAKAN CUSTOMER ID CRM
    # --------------------------------------------------------

    crm_customer_id = customer["customer_id"]

    # --------------------------------------------------------
    # FIND CONTACTS
    # --------------------------------------------------------

    docs = await db.contacts.find(
        {
            "customer_id": crm_customer_id
        }
    ).sort(
        "created_at",
        -1
    ).to_list(1000)

    return [
        Contact(**doc)
        for doc in docs
    ]
