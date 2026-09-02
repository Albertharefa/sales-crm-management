# ============================================================
# SALES CRM MANAGEMENT
# backend/routers/customers.py
# ============================================================

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from lib.db import db


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


# ============================================================
# HELPERS
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def serialize_document(
    document: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Convert MongoDB document into JSON-safe dictionary.
    """

    if document is None:
        return None

    result = dict(document)

    # Remove MongoDB internal ID
    result.pop("_id", None)

    return result


def serialize_documents(
    documents: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    return [
        serialize_document(document)
        for document in documents
    ]


# ============================================================
# CUSTOMER RESPONSE MODEL
# ============================================================

class Customer(BaseModel):
    """
    Customer response model.

    Compatible with current CRM MongoDB structure:
    id
    customer_id
    name
    company
    industry
    source
    city
    province
    phone
    email
    pic_name
    pic_position
    status
    sales_id
    sales_name
    address
    notes
    created_at
    updated_at
    """

    id: str
    customer_id: Optional[str] = None

    name: str

    # Company is optional because existing data may not have it
    company: Optional[str] = None

    industry: str = "Manufacturing"
    source: Optional[str] = None

    city: str = "Jakarta"
    province: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None

    pic_name: Optional[str] = None
    pic_position: Optional[str] = None

    status: str = "Active"

    sales_id: Optional[str] = None
    sales_name: Optional[str] = None

    address: Optional[str] = None
    notes: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================================
# CUSTOMER CREATE MODEL
# ============================================================

class CustomerCreate(BaseModel):

    customer_id: Optional[str] = None

    name: str = Field(
        min_length=2,
        description="Customer name",
    )

    company: Optional[str] = None

    industry: str = "Manufacturing"

    source: Optional[str] = None

    city: str = "Jakarta"

    province: Optional[str] = None

    phone: Optional[str] = None

    email: Optional[str] = None

    pic_name: Optional[str] = None

    pic_position: Optional[str] = None

    status: str = "Active"

    sales_id: Optional[str] = None

    address: Optional[str] = None

    notes: Optional[str] = None


# ============================================================
# CUSTOMER UPDATE MODEL
# ============================================================

class CustomerUpdate(BaseModel):

    name: Optional[str] = None

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

    address: Optional[str] = None

    notes: Optional[str] = None


# ============================================================
# CONTACT RESPONSE MODEL
# ============================================================

class Contact(BaseModel):

    id: str

    contact_id: Optional[str] = None

    customer_id: str

    customer_name: Optional[str] = None

    first_name: str

    last_name: Optional[str] = None

    position: Optional[str] = None

    department: Optional[str] = None

    email: Optional[str] = None

    mobile: Optional[str] = None

    contact_type: str = "User"

    is_decision_maker: bool = False

    status: str = "Active"

    notes: Optional[str] = None

    created_at: datetime

    updated_at: Optional[datetime] = None


# ============================================================
# CONTACT CREATE MODEL
# ============================================================

class ContactCreate(BaseModel):

    first_name: str = Field(
        min_length=1
    )

    last_name: Optional[str] = None

    position: Optional[str] = None

    department: Optional[str] = None

    email: Optional[str] = None

    mobile: Optional[str] = None

    contact_type: str = "User"

    is_decision_maker: bool = False

    status: str = "Active"

    notes: Optional[str] = None


# ============================================================
# CUSTOMER NORMALIZER
# ============================================================

def normalize_customer(
    document: Dict[str, Any]
) -> Dict[str, Any]:

    data = dict(document)

    # Remove MongoDB ObjectId
    data.pop("_id", None)

    # --------------------------------------------------------
    # CUSTOMER ID
    # --------------------------------------------------------

    if not data.get("customer_id"):
        data["customer_id"] = data.get("id")

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    # Current database uses "name".
    # Older data may use "company_name".
    if not data.get("name"):
        data["name"] = (
            data.get("company_name")
            or data.get("company")
            or "Unknown Customer"
        )

    # --------------------------------------------------------
    # COMPANY
    # --------------------------------------------------------

    if "company" not in data:
        data["company"] = data.get("company_name")

    # --------------------------------------------------------
    # DEFAULT VALUES
    # --------------------------------------------------------

    if not data.get("industry"):
        data["industry"] = "Manufacturing"

    if not data.get("city"):
        data["city"] = "Jakarta"

    if not data.get("status"):
        data["status"] = "Active"

    return data


# ============================================================
# CONTACT NORMALIZER
# ============================================================

def normalize_contact(
    document: Dict[str, Any],
    customer_name: Optional[str] = None,
) -> Dict[str, Any]:

    data = dict(document)

    data.pop("_id", None)

    if not data.get("contact_id"):
        data["contact_id"] = data.get("id")

    if not data.get("customer_name"):
        data["customer_name"] = customer_name

    if not data.get("contact_type"):
        data["contact_type"] = "User"

    if not data.get("status"):
        data["status"] = "Active"

    if "is_decision_maker" not in data:
        data["is_decision_maker"] = False

    return data


# ============================================================
# CUSTOMER ID GENERATOR
# ============================================================

async def generate_customer_id() -> str:
    """
    Generate customer ID:

    CUS-2026-00001
    CUS-2026-00002
    ...
    """

    year = utc_now().year

    prefix = f"CUS-{year}-"

    last_customer = await db.customers.find_one(
        {
            "$or": [
                {
                    "id": {
                        "$regex": f"^{prefix}"
                    }
                },
                {
                    "customer_id": {
                        "$regex": f"^{prefix}"
                    }
                },
            ]
        },
        sort=[
            ("id", -1)
        ],
    )

    if not last_customer:
        return f"{prefix}00001"

    last_id = (
        last_customer.get("id")
        or last_customer.get("customer_id")
        or ""
    )

    try:
        last_number = int(
            last_id.split("-")[-1]
        )

        next_number = last_number + 1

    except (ValueError, IndexError):

        next_number = 1

    return f"{prefix}{next_number:05d}"


# ============================================================
# CONTACT ID GENERATOR
# ============================================================

async def generate_contact_id() -> str:
    """
    Generate contact ID:

    CON-2026-00001
    CON-2026-00002
    ...
    """

    year = utc_now().year

    prefix = f"CON-{year}-"

    last_contact = await db.contacts.find_one(
        {
            "id": {
                "$regex": f"^{prefix}"
            }
        },
        sort=[
            ("id", -1)
        ],
    )

    if not last_contact:
        return f"{prefix}00001"

    last_id = last_contact.get(
        "id",
        ""
    )

    try:

        last_number = int(
            last_id.split("-")[-1]
        )

        next_number = last_number + 1

    except (ValueError, IndexError):

        next_number = 1

    return f"{prefix}{next_number:05d}"


# ============================================================
# GET /customers
# LIST CUSTOMERS
# ============================================================

@router.get(
    "",
    response_model=dict,
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
):

    try:

        # ----------------------------------------------------
        # TOTAL DATA
        # ----------------------------------------------------

        total = await db.customers.count_documents({})

        # ----------------------------------------------------
        # PAGINATION
        # ----------------------------------------------------

        skip = (
            page - 1
        ) * page_size

        # ----------------------------------------------------
        # GET DATA
        # ----------------------------------------------------

        documents = await db.customers.find(
            {}
        ).sort(
            "created_at",
            -1,
        ).skip(
            skip
        ).limit(
            page_size
        ).to_list(
            length=page_size
        )

        # ----------------------------------------------------
        # NORMALIZE
        # ----------------------------------------------------

        items = [
            normalize_customer(document)
            for document in documents
        ]

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (
                (total + page_size - 1)
                // page_size
            ),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to list customers: "
                f"{str(exc)}"
            ),
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
):

    try:

        now = utc_now()

        # ----------------------------------------------------
        # CUSTOMER ID
        # ----------------------------------------------------

        customer_id = payload.customer_id

        if not customer_id:

            customer_id = (
                await generate_customer_id()
            )

        # ----------------------------------------------------
        # CHECK DUPLICATE
        # ----------------------------------------------------

        existing = await db.customers.find_one(
            {
                "$or": [
                    {
                        "id": customer_id
                    },
                    {
                        "customer_id": customer_id
                    },
                ]
            }
        )

        if existing:

            raise HTTPException(
                status_code=409,
                detail=(
                    f"Customer {customer_id} "
                    "already exists."
                ),
            )

        # ----------------------------------------------------
        # CUSTOMER DOCUMENT
        # ----------------------------------------------------

        customer = {

            "id": customer_id,

            "customer_id": customer_id,

            "name": payload.name,

            "company": payload.company,

            "industry": payload.industry,

            "source": payload.source,

            "city": payload.city,

            "province": payload.province,

            "phone": payload.phone,

            "email": payload.email,

            "pic_name": payload.pic_name,

            "pic_position": payload.pic_position,

            "status": payload.status,

            "sales_id": payload.sales_id,

            "sales_name": None,

            "address": payload.address,

            "notes": payload.notes,

            "created_at": now,

            "updated_at": now,
        }

        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        await db.customers.insert_one(
            customer
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return normalize_customer(
            customer
        )

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to create customer: "
                f"{str(exc)}"
            ),
        )


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
):

    try:

        customer = await db.customers.find_one(
            {
                "$or": [
                    {
                        "id": customer_id
                    },
                    {
                        "customer_id": customer_id
                    },
                ]
            }
        )

        if not customer:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Customer {customer_id} "
                    "not found."
                ),
            )

        return normalize_customer(
            customer
        )

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to get customer: "
                f"{str(exc)}"
            ),
        )


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
    payload: CustomerUpdate,
):

    try:

        # ----------------------------------------------------
        # CHECK CUSTOMER
        # ----------------------------------------------------

        existing = await db.customers.find_one(
            {
                "$or": [
                    {
                        "id": customer_id
                    },
                    {
                        "customer_id": customer_id
                    },
                ]
            }
        )

        if not existing:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Customer {customer_id} "
                    "not found."
                ),
            )

        # ----------------------------------------------------
        # UPDATE DATA
        # ----------------------------------------------------

        update_data = payload.model_dump(
            exclude_unset=True
        )

        update_data["updated_at"] = utc_now()

        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        await db.customers.update_one(
            {
                "$or": [
                    {
                        "id": customer_id
                    },
                    {
                        "customer_id": customer_id
                    },
                ]
            },
            {
                "$set": update_data
            },
        )

        # ----------------------------------------------------
        # GET UPDATED DATA
        # ----------------------------------------------------

        updated_customer = await db.customers.find_one(
            {
                "$or": [
                    {
                        "id": customer_id
                    },
                    {
                        "customer_id": customer_id
                    },
                ]
            }
        )

        return normalize_customer(
            updated_customer
        )

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to update customer: "
                f"{str(exc)}"
            ),
        )


# ============================================================
# DELETE /customers/{customer_id}
# DELETE CUSTOMER
# ============================================================

@router.delete(
    "/{customer_id}",
    summary="Delete Customer",
)
async def delete_customer(
    customer_id: str,
):

    try:

        # ----------------------------------------------------
        # DELETE CUSTOMER
        # ----------------------------------------------------

        result = await db.customers.delete_one(
            {
                "$or": [
                    {
                        "id": customer_id
                    },
                    {
                        "customer_id": customer_id
                    },
                ]
            }
        )

        if result.deleted_count == 0:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Customer {customer_id} "
                    "not found."
                ),
            )

        # ----------------------------------------------------
        # DELETE RELATED CONTACTS
        # ----------------------------------------------------

        await db.contacts.delete_many(
            {
                "customer_id": customer_id
            }
        )

        return {
            "status": "success",
            "message": (
                f"Customer {customer_id} "
                "deleted successfully."
            ),
            "customer_id": customer_id,
        }

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to delete customer: "
                f"{str(exc)}"
            ),
        )


# ============================================================
# GET /customers/{customer_id}/contacts
# CUSTOMER CONTACTS
# ============================================================

@router.get(
    "/{customer_id}/contacts",
    response_model=List[Contact],
    summary="Customer Contacts",
)
async def get_customer_contacts(
    customer_id: str,
):

    try:

        # ----------------------------------------------------
        # CHECK CUSTOMER
        # ----------------------------------------------------

        customer = await db.customers.find_one(
            {
                "$or": [
                    {
                        "id": customer_id
                    },
                    {
                        "customer_id": customer_id
                    },
                ]
            }
        )

        if not customer:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Customer {customer_id} "
                    "not found."
                ),
            )

        customer_name = (
            customer.get("name")
            or customer.get("company_name")
            or customer.get("company")
        )

        # ----------------------------------------------------
        # GET CONTACTS
        # ----------------------------------------------------

        contacts = await db.contacts.find(
            {
                "customer_id": customer_id
            }
        ).sort(
            "created_at",
            -1,
        ).to_list(
            length=1000
        )

        # ----------------------------------------------------
        # NORMALIZE CONTACTS
        # ----------------------------------------------------

        return [
            normalize_contact(
                contact,
                customer_name,
            )
            for contact in contacts
        ]

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to get customer contacts: "
                f"{str(exc)}"
            ),
        )


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
):

    try:

        # ----------------------------------------------------
        # CHECK CUSTOMER
        # ----------------------------------------------------

        customer = await db.customers.find_one(
            {
                "$or": [
                    {
                        "id": customer_id
                    },
                    {
                        "customer_id": customer_id
                    },
                ]
            }
        )

        if not customer:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Customer {customer_id} "
                    "not found."
                ),
            )

        customer_name = (
            customer.get("name")
            or customer.get("company_name")
            or customer.get("company")
        )

        # ----------------------------------------------------
        # GENERATE CONTACT ID
        # ----------------------------------------------------

        contact_id = (
            await generate_contact_id()
        )

        now = utc_now()

        # ----------------------------------------------------
        # CONTACT DOCUMENT
        # ----------------------------------------------------

        contact = {

            "id": contact_id,

            "contact_id": contact_id,

            "customer_id": customer_id,

            "customer_name": customer_name,

            "first_name": payload.first_name,

            "last_name": payload.last_name,

            "position": payload.position,

            "department": payload.department,

            "email": payload.email,

            "mobile": payload.mobile,

            "contact_type": (
                payload.contact_type
                or "User"
            ),

            "is_decision_maker": (
                payload.is_decision_maker
            ),

            "status": (
                payload.status
                or "Active"
            ),

            "notes": payload.notes,

            "created_at": now,

            "updated_at": now,
        }

        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        await db.contacts.insert_one(
            contact
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return normalize_contact(
            contact,
            customer_name,
        )

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


# ============================================================
# ROUTER READY
# ============================================================

print(
    "INFO: ✓ routers.customers loaded"
)
