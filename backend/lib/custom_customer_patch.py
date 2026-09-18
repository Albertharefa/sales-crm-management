"""Compatibility patch for custom Customer Industry/Source values and
customer-detail contact loading.

The Customer form uses the special option `Lainnya` and a manually entered
value. Normalize that value before FastAPI/Pydantic validates the request so
MongoDB receives the actual text rather than the placeholder `Lainnya`.
"""

from typing import Any
import uuid

from fastapi import Depends, HTTPException

from lib.db import db
from routers import customers
from routers.deps import current_user


_CUSTOM_KEYS = {
    "industry": (
        "industry_other",
        "industry_custom",
        "custom_industry",
        "other_industry",
        "industryOther",
        "industryCustom",
        "customIndustry",
        "industry_lainnya",
    ),
    "source": (
        "source_other",
        "source_custom",
        "custom_source",
        "other_source",
        "sourceOther",
        "sourceCustom",
        "customSource",
        "source_lainnya",
    ),
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _custom_value(data: dict[str, Any], field: str) -> str:
    for key in _CUSTOM_KEYS[field]:
        value = _text(data.get(key))
        if value:
            return value
    return ""


def _normalize_payload(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    normalized = dict(data)
    for field in ("industry", "source"):
        if _text(normalized.get(field)).lower() == "lainnya":
            custom = _custom_value(normalized, field)
            if custom:
                normalized[field] = custom
    return normalized


def _patch_model(model: type) -> None:
    # FastAPI/Pydantic v2 normally validates through model_validate(), so
    # patching only __init__ is not sufficient for request bodies.
    original_init = model.__init__
    original_model_validate = model.model_validate

    def patched_init(self, **data: Any):
        original_init(self, **_normalize_payload(data))

    @classmethod
    def patched_model_validate(cls, obj: Any, *args: Any, **kwargs: Any):
        return original_model_validate(_normalize_payload(obj), *args, **kwargs)

    model.__init__ = patched_init
    model.model_validate = patched_model_validate


_patch_model(customers.CustomerCreate)
_patch_model(customers.CustomerUpdate)


# ============================================================
# CUSTOMER DETAIL CONTACTS
# ============================================================

@customers.router.get("/{customer_id}/contacts", summary="Get Customer Contacts")
async def get_customer_contacts(customer_id: str, user: dict = Depends(current_user)):
    """Return contacts linked to the selected customer.

    Customer detail links by the canonical public customer_id. Legacy contact
    records that still point at the customer's internal id are also accepted.

    If a manually-created customer has PIC data stored in the Customer record
    but no Contact record yet, create the primary Contact from those fields
    once, then return it. This keeps the Customer -> Contact relationship
    consistent for both demo and manually-entered customers without changing
    existing contact records.
    """
    ref = _text(customer_id)
    if not ref:
        raise HTTPException(status_code=400, detail="Customer ID wajib diisi")

    customer = await customers.find_customer(ref)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {ref} not found")

    await customers.ensure_customer_access(customer, user)

    canonical_id = _text(customer.get("customer_id")) or _text(customer.get("id"))
    internal_id = _text(customer.get("id"))
    if not canonical_id:
        return []

    customer_keys = []
    for value in (canonical_id, internal_id):
        if value and value not in customer_keys:
            customer_keys.append(value)

    contacts = await db.contacts.find(
        {"customer_id": {"$in": customer_keys}},
        {"_id": 0},
    ).sort("created_at", -1).to_list(100)

    # Manual Customer records can contain PIC information without a separate
    # Contact document. Materialize that primary contact so the DB relationship
    # is real and future screens can use the same contacts collection.
    if not contacts and any(_text(customer.get(field)) for field in ("pic_name", "email", "phone")):
        contact = {
            "id": str(uuid.uuid4()),
            "contact_id": f"CON-{canonical_id}",
            "customer_id": canonical_id,
            "customer_name": _text(customer.get("name")) or _text(customer.get("company_name")),
            "first_name": _text(customer.get("pic_name")),
            "last_name": "",
            "position": _text(customer.get("pic_position")),
            "department": "",
            "email": customer.get("email"),
            "mobile": customer.get("phone"),
            "contact_type": "Primary",
            "is_decision_maker": False,
            "status": _text(customer.get("status")) or "Active",
            "notes": "Primary contact created from Customer PIC information.",
            "created_at": customer.get("updated_at") or customer.get("created_at"),
        }
        await db.contacts.insert_one(contact)
        contact.pop("_id", None)
        contacts = [contact]

    return contacts
