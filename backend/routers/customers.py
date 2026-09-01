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
# 1. LIST CUSTOMERS
# ============================================================
@router.get("", response_model=Paginated)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    status: str | None = None,
    industry: str | None = None,
    user: dict = Depends(current_user),
):
    """
    Get customer list with pagination, search and filters.
    """

    query = {
        key: value
        for key, value in {
            "status": status,
            "industry": industry,
        }.items()
        if value
    }

    from routers.common import page_collection

    return await page_collection(
        "customers",
        page,
        page_size,
        search,
        query,
    )


# ============================================================
# 2. CREATE CUSTOMER
# ============================================================
@router.post("", response_model=Customer)
async def create_customer(
    payload: CustomerCreate,
    user: dict = Depends(current_user),
):
    """
    Create a new customer.
    """

    # --------------------------------------------------------
    # Check duplicate customer name
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
    # Generate Customer ID
    # Example: CUS-2026-00001
    # --------------------------------------------------------
    count = await db.customers.count_documents({}) + 1

    customer_id = f"CUS-{now().year}-{count:05d}"

    # --------------------------------------------------------
    # Create document
    # --------------------------------------------------------
    doc = {
        "id": new_id(),
        "customer_id": customer_id,
        **payload.model_dump(mode="json"),
        "sales_name": user.get("name"),
        "created_at": now(),
        "updated_at": now(),
    }

    # --------------------------------------------------------
    # Save to database
    # --------------------------------------------------------
    await db.customers.insert_one(doc)

    # --------------------------------------------------------
    # Audit log
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
# 3. GET CUSTOMER BY CUSTOMER ID
# ============================================================
@router.get("/{customer_id}", response_model=Customer)
async def get_customer(
    customer_id: str,
    user: dict = Depends(current_user),
):
    """
    Get customer detail using customer_id.

    Example:
    /customers/CUS-2026-00001
    """

    # IMPORTANT:
    # customer_id dari URL harus dicari pada field
    # "customer_id", BUKAN "id".
    doc = await db.customers.find_one(
        {
            "customer_id": customer_id
        }
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    return Customer(**doc)


# ============================================================
# 4. UPDATE CUSTOMER
# ============================================================
@router.put("/{customer_id}", response_model=Customer)
async def update_customer(
    customer_id: str,
    payload: CustomerCreate,
    user: dict = Depends(current_user),
):
    """
    Update customer using customer_id.
    """

    # --------------------------------------------------------
    # Find customer using customer_id
    # --------------------------------------------------------
    doc = await db.customers.find_one(
        {
            "customer_id": customer_id
        }
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    # --------------------------------------------------------
    # Check duplicate name
    # --------------------------------------------------------
    duplicate = await db.customers.find_one(
        {
            "name": {
                "$regex": f"^{payload.name}$",
                "$options": "i",
            },
            "customer_id": {
                "$ne": customer_id
            },
        }
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Customer dengan nama tersebut sudah ada",
        )

    # --------------------------------------------------------
    # Prepare update
    # --------------------------------------------------------
    update = {
        **payload.model_dump(mode="json"),
        "updated_at": now(),
    }

    # --------------------------------------------------------
    # Update database
    # --------------------------------------------------------
    await db.customers.update_one(
        {
            "customer_id": customer_id
        },
        {
            "$set": update
        },
    )

    # --------------------------------------------------------
    # Audit log
    # --------------------------------------------------------
    await audit(
        user,
        "Update",
        "Customers",
        doc["id"],
        {
            "customer_id": customer_id,
            **update,
        },
    )

    # --------------------------------------------------------
    # Return updated customer
    # --------------------------------------------------------
    return Customer(
        **{
            **doc,
            **update,
        }
    )


# ============================================================
# 5. DELETE CUSTOMER
# ============================================================
@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: str,
    user: dict = Depends(current_user),
):
    """
    Delete customer using customer_id.
    """

    # --------------------------------------------------------
    # Find customer first
    # --------------------------------------------------------
    doc = await db.customers.find_one(
        {
            "customer_id": customer_id
        }
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    # --------------------------------------------------------
    # Delete customer
    # --------------------------------------------------------
    result = await db.customers.delete_one(
        {
            "customer_id": customer_id
        }
    )

    if not result.deleted_count:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    # --------------------------------------------------------
    # Audit log
    # --------------------------------------------------------
    await audit(
        user,
        "Delete",
        "Customers",
        doc["id"],
        {
            "customer_id": customer_id,
            "name": doc.get("name"),
        },
    )


# ============================================================
# 6. GET CUSTOMER CONTACTS
# ============================================================
@router.get(
    "/{customer_id}/contacts",
    response_model=list[Contact],
)
async def customer_contacts(
    customer_id: str,
    user: dict = Depends(current_user),
):
    """
    Get all contacts belonging to a customer.
    """

    # --------------------------------------------------------
    # Make sure customer exists
    # --------------------------------------------------------
    customer = await db.customers.find_one(
        {
            "customer_id": customer_id
        }
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    # --------------------------------------------------------
    # Get contacts
    # --------------------------------------------------------
    docs = await db.contacts.find(
        {
            "customer_id": customer_id
        }
    ).sort(
        "created_at",
        -1,
    ).to_list(1000)

    return [
        Contact(**doc)
        for doc in docs
    ]
