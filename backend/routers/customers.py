from fastapi import APIRouter, Depends, HTTPException, Query

from lib.db import db
from models.crm import (
    Customer,
    CustomerCreate,
    Paginated,
    Contact,
    ContactCreate,
)
from routers.common import audit, new_id, now
from routers.deps import current_user


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


# ============================================================
# GET /customers
# LIST CUSTOMERS
# ============================================================

@router.get(
    "",
    response_model=Paginated,
    summary="List Customers",
)
async def list_customers(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=25,
        ge=1,
        le=100,
    ),
    search: str = "",
    status: str | None = None,
    industry: str | None = None,
    user: dict = Depends(current_user),
):
    """
    Get paginated customer list.
    """

    from routers.common import page_collection

    query = {
        key: value
        for key, value in {
            "status": status,
            "industry": industry,
        }.items()
        if value
    }

    return await page_collection(
        "customers",
        page,
        page_size,
        search,
        query,
    )


# ============================================================
# POST /customers
# CREATE CUSTOMER
# ============================================================

@router.post(
    "",
    response_model=Customer,
    summary="Create Customer",
)
async def create_customer(
    payload: CustomerCreate,
    user: dict = Depends(current_user),
):
    """
    Create a new customer.
    """

    # --------------------------------------------------------
    # CHECK DUPLICATE CUSTOMER
    # --------------------------------------------------------

    duplicate = await db.customers.find_one(
        {
            "name": {
                "$regex": f"^{payload.name}$",
                "$options": "i",
            }
        }
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Customer dengan nama tersebut sudah ada",
        )

    # --------------------------------------------------------
    # GENERATE CUSTOMER NUMBER
    # --------------------------------------------------------

    count = await db.customers.count_documents({}) + 1

    customer_id = (
        f"CUS-{now().year}-{count:05d}"
    )

    # --------------------------------------------------------
    # BUILD DOCUMENT
    # --------------------------------------------------------

    timestamp = now()

    doc = {
        "id": new_id(),
        "customer_id": customer_id,
        **payload.model_dump(mode="json"),
        "sales_name": user.get("name"),
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    # --------------------------------------------------------
    # INSERT
    # --------------------------------------------------------

    await db.customers.insert_one(doc)

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    await audit(
        user,
        "Create",
        "Customers",
        doc["id"],
        {
            "name": doc["name"],
            "customer_id": doc["customer_id"],
        },
    )

    return Customer(**doc)


# ============================================================
# GET /customers/{customer_id}
# GET CUSTOMER
# ============================================================

@router.get(
    "/{customer_id}",
    response_model=Customer,
    summary="Get Customer",
)
async def get_customer(
    customer_id: str,
    user: dict = Depends(current_user),
):
    """
    Get one customer by customer_id or internal id.
    """

    doc = await db.customers.find_one(
        {
            "$or": [
                {"id": customer_id},
                {"customer_id": customer_id},
            ]
        }
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    return Customer(**doc)


# ============================================================
# PUT /customers/{customer_id}
# UPDATE CUSTOMER
# ============================================================

@router.put(
    "/{customer_id}",
    response_model=Customer,
    summary="Update Customer",
)
async def update_customer(
    customer_id: str,
    payload: CustomerCreate,
    user: dict = Depends(current_user),
):
    """
    Update an existing customer.
    """

    # --------------------------------------------------------
    # FIND CUSTOMER
    # --------------------------------------------------------

    doc = await db.customers.find_one(
        {
            "$or": [
                {"id": customer_id},
                {"customer_id": customer_id},
            ]
        }
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    # --------------------------------------------------------
    # CHECK DUPLICATE NAME
    # --------------------------------------------------------

    duplicate = await db.customers.find_one(
        {
            "name": {
                "$regex": f"^{payload.name}$",
                "$options": "i",
            },
            "id": {
                "$ne": doc["id"],
            },
        }
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Customer dengan nama tersebut sudah ada",
        )

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    update = {
        **payload.model_dump(mode="json"),
        "updated_at": now(),
    }

    await db.customers.update_one(
        {"id": doc["id"]},
        {"$set": update},
    )

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    await audit(
        user,
        "Update",
        "Customers",
        doc["id"],
        update,
    )

    # --------------------------------------------------------
    # RETURN UPDATED DOCUMENT
    # --------------------------------------------------------

    updated_doc = {
        **doc,
        **update,
    }

    return Customer(**updated_doc)


# ============================================================
# DELETE /customers/{customer_id}
# DELETE CUSTOMER
# ============================================================

@router.delete(
    "/{customer_id}",
    status_code=204,
    summary="Delete Customer",
)
async def delete_customer(
    customer_id: str,
    user: dict = Depends(current_user),
):
    """
    Delete a customer.
    """

    # --------------------------------------------------------
    # FIND CUSTOMER
    # --------------------------------------------------------

    doc = await db.customers.find_one(
        {
            "$or": [
                {"id": customer_id},
                {"customer_id": customer_id},
            ]
        }
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    result = await db.customers.delete_one(
        {"id": doc["id"]}
    )

    if not result.deleted_count:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    await audit(
        user,
        "Delete",
        "Customers",
        doc["id"],
        {
            "name": doc.get("name"),
            "customer_id": doc.get("customer_id"),
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
    summary="Get Customer Contacts",
)
async def customer_contacts(
    customer_id: str,
    user: dict = Depends(current_user),
):
    """
    Get all contacts belonging to a customer.
    """

    # --------------------------------------------------------
    # CHECK CUSTOMER
    # --------------------------------------------------------

    customer = await db.customers.find_one(
        {
            "$or": [
                {"id": customer_id},
                {"customer_id": customer_id},
            ]
        }
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    # --------------------------------------------------------
    # USE CUSTOMER_ID STORED ON CONTACT
    # --------------------------------------------------------

    lookup_customer_id = customer.get(
        "customer_id",
        customer_id,
    )

    docs = await (
        db.contacts
        .find(
            {
                "customer_id": lookup_customer_id,
            },
            {
                "_id": 0,
            },
        )
        .sort(
            "created_at",
            -1,
        )
        .to_list(1000)
    )

    return [
        Contact(**doc)
        for doc in docs
    ]


# ============================================================
# POST /customers/{customer_id}/contacts
# CREATE CUSTOMER CONTACT
# ============================================================

@router.post(
    "/{customer_id}/contacts",
    response_model=Contact,
    summary="Create Customer Contact",
)
async def create_customer_contact(
    customer_id: str,
    payload: ContactCreate,
    user: dict = Depends(current_user),
):
    """
    Create a new contact for an existing customer.
    """

    # --------------------------------------------------------
    # CHECK CUSTOMER
    # --------------------------------------------------------

    customer = await db.customers.find_one(
        {
            "$or": [
                {"id": customer_id},
                {"customer_id": customer_id},
            ]
        }
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    # --------------------------------------------------------
    # USE CUSTOMER_ID FROM CUSTOMER RECORD
    # --------------------------------------------------------

    real_customer_id = customer.get(
        "customer_id",
        customer_id,
    )

    # --------------------------------------------------------
    # CREATE CONTACT THROUGH SERVICE
    # --------------------------------------------------------

    try:
        from services.contacts import (
            create_customer_contact as service_create
        )

        result = await service_create(
            customer_id=real_customer_id,
            payload=payload,
        )

        # ----------------------------------------------------
        # AUDIT
        # ----------------------------------------------------

        await audit(
            user,
            "Create",
            "Contacts",
            result.get("id"),
            {
                "customer_id": real_customer_id,
                "contact_id": result.get("contact_id"),
                "first_name": result.get("first_name"),
                "last_name": result.get("last_name"),
            },
        )

        return Contact(**result)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to create customer contact: "
                f"{str(exc)}"
            ),
        )
