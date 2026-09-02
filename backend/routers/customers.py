# ============================================================
# SALES CRM MANAGEMENT
# backend/routers/customers.py
# ============================================================

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
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


def serialize_document(document: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Convert MongoDB document into JSON-safe dictionary.
    """

    if document is None:
        return None

    result = dict(document)

    if "_id" in result:
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
# CUSTOMER MODELS
# ============================================================

class CustomerCreate(BaseModel):
    customer_id: Optional[str] = None
    company_name: str
    customer_type: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = "Indonesia"

    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    status: Optional[str] = "Active"
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    company_name: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    status: Optional[str] = None
    notes: Optional[str] = None


class Customer(CustomerCreate):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================================
# CONTACT MODELS
# ============================================================

class ContactCreate(BaseModel):
    first_name: str
    last_name: Optional[str] = None

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[str] = None
    mobile: Optional[str] = None
    contact_type: Optional[str] = "User"

    is_decision_maker: bool = False
    status: Optional[str] = "Active"
    notes: Optional[str] = None


class Contact(ContactCreate):
    id: str
    customer_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================================
# CUSTOMER ID GENERATOR
# ============================================================

async def generate_customer_id() -> str:
    """
    Generate customer ID:
    CUS-2026-00001
    """

    year = utc_now().year
    prefix = f"CUS-{year}-"

    last_customer = await db.customers.find_one(
        {
            "id": {
                "$regex": f"^{prefix}"
            }
        },
        sort=[
            ("id", -1)
        ],
    )

    if not last_customer:
        return f"{prefix}00001"

    last_id = last_customer.get("id", "")

    try:
        last_number = int(last_id.split("-")[-1])
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

    last_id = last_contact.get("id", "")

    try:
        last_number = int(last_id.split("-")[-1])
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
    response_model=List[Customer],
    summary="List Customers",
)
async def list_customers():
    try:
        documents = await db.customers.find(
            {}
        ).sort(
            "created_at",
            -1,
        ).to_list(
            length=1000
        )

        return serialize_documents(documents)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list customers: {str(exc)}",
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

        customer_id = payload.customer_id

        if not customer_id:
            customer_id = await generate_customer_id()

        existing = await db.customers.find_one(
            {
                "id": customer_id
            }
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Customer {customer_id} already exists.",
            )

        customer = {
            "id": customer_id,
            "company_name": payload.company_name,
            "customer_type": payload.customer_type,
            "industry": payload.industry,
            "address": payload.address,
            "city": payload.city,
            "province": payload.province,
            "country": payload.country,

            "phone": payload.phone,
            "email": payload.email,
            "website": payload.website,

            "status": payload.status or "Active",
            "notes": payload.notes,

            "created_at": now,
            "updated_at": now,
        }

        await db.customers.insert_one(
            customer
        )

        return serialize_document(
            customer
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create customer: {str(exc)}",
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
                "id": customer_id
            }
        )

        if not customer:
            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found.",
            )

        return serialize_document(
            customer
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get customer: {str(exc)}",
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
        existing = await db.customers.find_one(
            {
                "id": customer_id
            }
        )

        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found.",
            )

        update_data = payload.model_dump(
            exclude_unset=True
        )

        update_data["updated_at"] = utc_now()

        await db.customers.update_one(
            {
                "id": customer_id
            },
            {
                "$set": update_data
            },
        )

        updated_customer = await db.customers.find_one(
            {
                "id": customer_id
            }
        )

        return serialize_document(
            updated_customer
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update customer: {str(exc)}",
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
        existing = await db.customers.find_one(
            {
                "id": customer_id
            }
        )

        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found.",
            )

        result = await db.customers.delete_one(
            {
                "id": customer_id
            }
        )

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found.",
            )

        # Delete related contacts as well
        await db.contacts.delete_many(
            {
                "customer_id": customer_id
            }
        )

        return {
            "status": "success",
            "message": f"Customer {customer_id} deleted successfully.",
            "customer_id": customer_id,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete customer: {str(exc)}",
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
        customer = await db.customers.find_one(
            {
                "id": customer_id
            }
        )

        if not customer:
            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found.",
            )

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

        return serialize_documents(
            contacts
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get customer contacts: {str(exc)}",
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
        # Check customer
        # ----------------------------------------------------

        customer = await db.customers.find_one(
            {
                "id": customer_id
            }
        )

        if not customer:
            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found.",
            )

        # ----------------------------------------------------
        # Generate contact ID
        # ----------------------------------------------------

        contact_id = await generate_contact_id()

        now = utc_now()

        # ----------------------------------------------------
        # Create contact
        # ----------------------------------------------------

        contact = {
            "id": contact_id,
            "customer_id": customer_id,

            "first_name": payload.first_name,
            "last_name": payload.last_name,

            "position": payload.position,
            "department": payload.department,

            "email": payload.email,
            "mobile": payload.mobile,

            "contact_type": payload.contact_type or "User",
            "is_decision_maker": payload.is_decision_maker,

            "status": payload.status or "Active",
            "notes": payload.notes,

            "created_at": now,
            "updated_at": now,
        }

        await db.contacts.insert_one(
            contact
        )

        return serialize_document(
            contact
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create customer contact: {str(exc)}",
        )


# ============================================================
# ROUTER READY
# ============================================================

print("INFO: ✓ routers.customers loaded")
