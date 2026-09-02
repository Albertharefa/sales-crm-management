from datetime import datetime, timezone
import secrets

from fastapi import HTTPException

from lib.db import db


# ============================================================
# HELPERS
# ============================================================

def now():
    return datetime.now(timezone.utc)


def new_id():
    return secrets.token_hex(16)


# ============================================================
# FIND CUSTOMER
# ============================================================

async def find_customer(customer_id: str):
    """
    Find customer using the public customer_id.

    Primary field:
        customer_id

    Fallback:
        id
    """

    if not customer_id:
        return None

    # --------------------------------------------------------
    # NORMALIZE INPUT
    # --------------------------------------------------------

    customer_id = str(customer_id).strip()

    # --------------------------------------------------------
    # TRY customer_id
    # --------------------------------------------------------

    customer = await db.customers.find_one(
        {
            "customer_id": customer_id
        },
        {
            "_id": 0
        },
    )

    if customer:
        return customer

    # --------------------------------------------------------
    # FALLBACK: TRY id
    # --------------------------------------------------------

    customer = await db.customers.find_one(
        {
            "id": customer_id
        },
        {
            "_id": 0
        },
    )

    if customer:
        return customer

    # --------------------------------------------------------
    # FALLBACK: CASE-INSENSITIVE customer_id
    # --------------------------------------------------------

    customer = await db.customers.find_one(
        {
            "customer_id": {
                "$regex": f"^{customer_id}$",
                "$options": "i",
            }
        },
        {
            "_id": 0
        },
    )

    return customer


# ============================================================
# CREATE CUSTOMER CONTACT
# ============================================================

async def create_customer_contact(
    customer_id: str,
    payload,
):
    """
    Create a new contact for an existing customer.
    """

    # --------------------------------------------------------
    # NORMALIZE CUSTOMER ID
    # --------------------------------------------------------

    customer_id = str(customer_id).strip()

    # --------------------------------------------------------
    # CHECK CUSTOMER
    # --------------------------------------------------------

    customer = await find_customer(customer_id)

    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found",
        )

    # --------------------------------------------------------
    # GET ACTUAL CUSTOMER ID
    # --------------------------------------------------------

    actual_customer_id = customer.get(
        "customer_id",
        customer_id,
    )

    # --------------------------------------------------------
    # GET CUSTOMER NAME
    # --------------------------------------------------------

    customer_name = customer.get("name")

    if not customer_name:
        customer_name = customer.get("company_name", "")

    # --------------------------------------------------------
    # PREPARE CONTACT ID
    # --------------------------------------------------------

    created_at = now()

    contact_id = (
        "CON-"
        + datetime.now(timezone.utc).strftime("%Y%m%d")
        + "-"
        + secrets.token_hex(3).upper()
    )

    # --------------------------------------------------------
    # PREPARE CONTACT DATA
    # --------------------------------------------------------

    contact = {
        "id": new_id(),

        "contact_id": contact_id,

        "customer_id": actual_customer_id,

        "customer_name": customer_name,

        "first_name": payload.first_name,

        "last_name": payload.last_name,

        "position": payload.position,

        "department": payload.department,

        "email": (
            str(payload.email)
            if payload.email
            else None
        ),

        "mobile": payload.mobile,

        "contact_type": payload.contact_type,

        "is_decision_maker": payload.is_decision_maker,

        "status": payload.status,

        "notes": payload.notes,

        "created_at": created_at,
    }

    # --------------------------------------------------------
    # SAVE TO MONGODB
    # --------------------------------------------------------

    await db.contacts.insert_one(contact)

    # --------------------------------------------------------
    # REMOVE MONGODB INTERNAL ID
    # --------------------------------------------------------

    contact.pop("_id", None)

    return contact


# ============================================================
# GET CUSTOMER CONTACTS
# ============================================================

async def get_customer_contacts(
    customer_id: str,
):
    """
    Get all contacts belonging to a customer.
    """

    customer_id = str(customer_id).strip()

    # --------------------------------------------------------
    # VERIFY CUSTOMER EXISTS
    # --------------------------------------------------------

    customer = await find_customer(customer_id)

    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found",
        )

    # --------------------------------------------------------
    # USE ACTUAL CUSTOMER ID
    # --------------------------------------------------------

    actual_customer_id = customer.get(
        "customer_id",
        customer_id,
    )

    # --------------------------------------------------------
    # GET CONTACTS
    # --------------------------------------------------------

    contacts = await db.contacts.find(
        {
            "customer_id": actual_customer_id
        },
        {
            "_id": 0
        },
    ).sort(
        "created_at",
        -1,
    ).to_list(100)

    return contacts
