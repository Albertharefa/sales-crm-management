from datetime import datetime, timezone
import secrets

from fastapi import HTTPException

from lib.db import db


# ============================================================
# CUSTOMER CONTACT SERVICE
# ============================================================


def _serialize_contact(contact: dict) -> dict:
    """
    Remove MongoDB internal _id before returning data.
    """
    contact.pop("_id", None)
    return contact


# ============================================================
# GET CUSTOMER CONTACTS
# ============================================================

async def get_customer_contacts(customer_id: str) -> list[dict]:
    """
    Get all contacts belonging to a customer.
    """

    # --------------------------------------------------------
    # Pastikan customer exists
    # --------------------------------------------------------

    customer = await db.customers.find_one(
        {"customer_id": customer_id},
        {"_id": 0, "customer_id": 1, "name": 1},
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found",
        )

    # --------------------------------------------------------
    # Ambil contacts
    # --------------------------------------------------------

    contacts = await (
        db.contacts
        .find(
            {"customer_id": customer_id},
            {"_id": 0},
        )
        .sort("created_at", -1)
        .to_list(500)
    )

    return contacts


# ============================================================
# CREATE CUSTOMER CONTACT
# ============================================================

async def create_customer_contact(
    customer_id: str,
    payload,
) -> dict:
    """
    Create a new contact for an existing customer.
    """

    # --------------------------------------------------------
    # Pastikan customer exists
    # --------------------------------------------------------

    customer = await db.customers.find_one(
        {"customer_id": customer_id},
        {"_id": 0, "customer_id": 1, "name": 1},
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found",
        )

    # --------------------------------------------------------
    # Convert Pydantic model ke dictionary
    # --------------------------------------------------------

    if hasattr(payload, "model_dump"):
        data = payload.model_dump()
    elif hasattr(payload, "dict"):
        data = payload.dict()
    else:
        data = dict(payload)

    # --------------------------------------------------------
    # Generate unique IDs
    # --------------------------------------------------------

    contact_id = (
        f"CON-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        f"-{secrets.token_hex(4).upper()}"
    )

    internal_id = secrets.token_hex(16)

    now = datetime.now(timezone.utc)

    # --------------------------------------------------------
    # Build contact document
    # --------------------------------------------------------

    contact = {
        "id": internal_id,
        "contact_id": contact_id,

        "customer_id": customer_id,
        "customer_name": customer.get("name", ""),

        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "position": data.get("position"),
        "department": data.get("department"),

        "email": data.get("email"),
        "mobile": data.get("mobile"),

        "contact_type": data.get(
            "contact_type",
            "User",
        ),

        "is_decision_maker": data.get(
            "is_decision_maker",
            False,
        ),

        "status": data.get(
            "status",
            "Active",
        ),

        "notes": data.get("notes"),

        "created_at": now,
    }

    # --------------------------------------------------------
    # Save to MongoDB
    # --------------------------------------------------------

    await db.contacts.insert_one(contact)

    # --------------------------------------------------------
    # Return clean response
    # --------------------------------------------------------

    return _serialize_contact(contact)


# ============================================================
# ALIAS
# ============================================================

async def create_contact(
    customer_id: str,
    payload,
) -> dict:
    """
    Alias untuk kompatibilitas dengan router.
    """

    return await create_customer_contact(
        customer_id=customer_id,
        payload=payload,
    )
