# ============================================================
# backend/routes/customers.py
# SALES CRM MANAGEMENT
# CUSTOMER ROUTES
# ============================================================

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import csv
import io
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict

from lib.db import db
from routers.deps import current_user


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
    dependencies=[Depends(current_user)],
)


# ============================================================
# HELPERS
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# EXPORT CUSTOMERS
# ============================================================

@router.get(
    "/export",
    summary="Export Customers CSV",
)
async def export_customers():
    """
    Export seluruh customer ke CSV dengan susunan kolom standar CRM.
    """

    columns = [
        "created_at",
        "customer_id",
        "company_name",
        "name PIC",
        "phone",
        "pic_position",
        "address",
        "city",
        "province",
        "email",
        "industry",
        "notes",
        "Sales_Name",
        "sales_id",
        "source",
        "status",
    ]

    cursor = db.customers.find(
        {},
        {"_id": 0},
    ).sort("created_at", -1)

    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(columns)

    async for raw_customer in cursor:
        customer = normalize_customer(raw_customer)

        created_at = customer.get("created_at")
        if isinstance(created_at, datetime):
            created_at_value = (
                f"{created_at.month}/{created_at.day}/{created_at.year}"
            )
        elif created_at:
            try:
                parsed = datetime.fromisoformat(
                    str(created_at).replace("Z", "+00:00")
                )
                created_at_value = (
                    f"{parsed.month}/{parsed.day}/{parsed.year}"
                )
            except ValueError:
                created_at_value = str(created_at)
        else:
            created_at_value = ""

        writer.writerow([
            created_at_value,
            customer.get("customer_id", ""),
            customer.get("company_name", ""),
            customer.get("pic_name", ""),
            customer.get("phone", ""),
            customer.get("pic_position", ""),
            customer.get("address", ""),
            customer.get("city", ""),
            customer.get("province", ""),
            customer.get("email", ""),
            customer.get("industry", ""),
            customer.get("notes", ""),
            customer.get("sales_name", ""),
            customer.get("sales_id", ""),
            customer.get("source", ""),
            customer.get("status", ""),
        ])

    content = "\ufeff" + buffer.getvalue()

    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="customers.csv"'
        },
    )


# ============================================================
# NORMALIZE CUSTOMER
# ============================================================

def normalize_customer(
    data: Dict[str, Any],
) -> Dict[str, Any]:

    item = dict(data)

    company_name = (
        item.get("company_name")
        or item.get("company")
        or ""
    )

    item["company_name"] = company_name

    if not item.get("company"):
        item["company"] = company_name

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
    item.setdefault("address", "")
    item.setdefault("notes", "")
    item.setdefault("sales_name", "")

    return item


# ============================================================
# FIND CUSTOMER
# ============================================================

async def find_customer(
    customer_id: str,
):

    if not customer_id:
        return None

    customer_id = str(
        customer_id
    ).strip()

    # --------------------------------------------------------
    # TRY PUBLIC CUSTOMER ID
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
    # TRY INTERNAL ID
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
    # CASE INSENSITIVE CUSTOMER ID
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
# FIND CONTACT
# ============================================================

async def find_contact(
    customer_id: str,
    contact_id: str,
):

    customer = await find_customer(
        customer_id
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found.",
        )

    actual_customer_id = (
        customer.get("customer_id")
        or customer_id
    )

    contact_id = str(
        contact_id
    ).strip()

    # --------------------------------------------------------
    # FIND CONTACT BY ID + CUSTOMER
    # --------------------------------------------------------

    contact = await db.contacts.find_one(
        {
            "$or": [
                {
                    "id": contact_id
                },
                {
                    "contact_id": contact_id
                },
            ],
            "customer_id": actual_customer_id,
        },
        {
            "_id": 0
        },
    )

    return contact


# ============================================================
# CUSTOMER RESPONSE MODEL
# ============================================================

class Customer(BaseModel):

    model_config = ConfigDict(
        extra="ignore"
    )

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


# ============================================================
# PAGINATED CUSTOMER RESPONSE
# ============================================================

class PaginatedCustomers(BaseModel):
    items: List[Customer]
    page: int
    page_size: int
    total: int


# ============================================================
# CUSTOMER CREATE
# ============================================================

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


# ============================================================
# CUSTOMER UPDATE
# ============================================================

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
# CONTACT RESPONSE MODEL
# ============================================================

class Contact(BaseModel):

    model_config = ConfigDict(
        extra="ignore"
    )

    id: str
    customer_id: str

    first_name: str = ""
    last_name: str = ""

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[str] = None
    mobile: Optional[str] = None

    contact_type: str = "User"

    is_decision_maker: bool = False

    status: str = "Active"

    notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================
# CONTACT CREATE / UPDATE
# ============================================================

class ContactCreate(BaseModel):

    first_name: str = ""
    last_name: str = ""

    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[str] = None
    mobile: Optional[str] = None

    contact_type: str = "User"

    is_decision_maker: bool = False

    status: str = "Active"

    notes: Optional[str] = None


# ============================================================
# GENERATE CUSTOMER ID
# ============================================================

async def generate_customer_id() -> str:

    year = utc_now().year

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

    last_id = last_customer.get(
        "customer_id",
        ""
    )

    try:

        last_number = int(
            last_id.split("-")[-1]
        )

        next_number = (
            last_number + 1
        )

    except Exception:

        next_number = 1

    return f"{prefix}{next_number:05d}"


# ============================================================
# GET /customers
# LIST CUSTOMERS
# ============================================================

@router.get(
    "",
    response_model=PaginatedCustomers,
    summary="List Customers",
)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = Query(""),
    status: str = Query(""),
    industry: str = Query(""),
    sales_name: str = Query(""),
):
    try:
        filters: Dict[str, Any] = {}

        if search.strip():
            term = search.strip()
            filters["$or"] = [
                {"name": {"$regex": term, "$options": "i"}},
                {"company_name": {"$regex": term, "$options": "i"}},
                {"company": {"$regex": term, "$options": "i"}},
                {"customer_id": {"$regex": term, "$options": "i"}},
                {"pic_name": {"$regex": term, "$options": "i"}},
                {"email": {"$regex": term, "$options": "i"}},
            ]

        if status.strip() and status.strip().lower() != "semua status":
            filters["status"] = status.strip()

        if industry.strip() and industry.strip().lower() != "semua industri":
            filters["industry"] = industry.strip()

        if sales_name.strip() and sales_name.strip().lower() != "semua sales":
            filters["sales_name"] = sales_name.strip()

        total = await db.customers.count_documents(filters)
        skip = (page - 1) * page_size

        customers = await (
            db.customers.find(filters, {"_id": 0})
            .sort([("created_at", -1), ("customer_id", -1)])
            .skip(skip)
            .limit(page_size)
            .to_list(length=page_size)
        )

        items = [
            Customer.model_validate(normalize_customer(customer))
            for customer in customers
        ]

        return PaginatedCustomers(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
        )

    except Exception as exc:
        print(f"ERROR: GET /customers failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list customers: {str(exc)}",
        )


# ============================================================
# GET /customers/sales-options
# SALES ASSIGNED TO CUSTOMERS
# ============================================================

@router.get(
    "/sales-options",
    response_model=List[str],
    summary="List Sales Assigned to Customers",
)
async def customer_sales_options():
    sales = await db.customers.distinct("sales_name")
    return sorted(
        {
            str(name).strip()
            for name in sales
            if name is not None and str(name).strip()
        },
        key=str.casefold,
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

        customer = await find_customer(
            customer_id
        )

        if not customer:

            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found.",
            )

        normalized = normalize_customer(
            customer
        )

        return Customer.model_validate(
            normalized
        )

    except HTTPException:
        raise

    except Exception as exc:

        print(
            f"ERROR: GET /customers/{customer_id} failed: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to get customer: {str(exc)}",
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

        customer_id = await generate_customer_id()

        company_name = (
            payload.company_name
            or payload.company
            or ""
        )

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

            "sales_id": payload.sales_id,

            "sales_name": payload.sales_name,

            "address": payload.address,

            "notes": payload.notes,

            "created_at": now,

            "updated_at": now,
        }

        await db.customers.insert_one(
            customer
        )

        normalized = normalize_customer(
            customer
        )

        return Customer.model_validate(
            normalized
        )

    except Exception as exc:

        print(
            f"ERROR: POST /customers failed: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to create customer: {str(exc)}",
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
                "$or": [
                    {
                        "customer_id": customer_id
                    },
                    {
                        "id": customer_id
                    },
                ]
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

        if (
            "company_name" in update_data
            and update_data["company_name"] is not None
        ):

            update_data["company"] = (
                update_data["company_name"]
            )

        elif (
            "company" in update_data
            and update_data["company"] is not None
        ):

            update_data["company_name"] = (
                update_data["company"]
            )

        update_data["updated_at"] = utc_now()

        await db.customers.update_one(
            {
                "_id": existing["_id"]
            },
            {
                "$set": update_data
            }
        )

        updated = await db.customers.find_one(
            {
                "_id": existing["_id"]
            }
        )

        normalized = normalize_customer(
            updated
        )

        return Customer.model_validate(
            normalized
        )

    except HTTPException:
        raise

    except Exception as exc:

        print(
            f"ERROR: PUT /customers/{customer_id} failed: {exc}"
        )

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
                "$or": [
                    {
                        "customer_id": customer_id
                    },
                    {
                        "id": customer_id
                    },
                ]
            }
        )

        if not existing:

            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found.",
            )

        await db.customers.delete_one(
            {
                "_id": existing["_id"]
            }
        )

        return {
            "status": "success",
            "message": "Customer deleted successfully",
            "customer_id": customer_id,
        }

    except HTTPException:
        raise

    except Exception as exc:

        print(
            f"ERROR: DELETE /customers/{customer_id} failed: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete customer: {str(exc)}",
        )


# ============================================================
# GET /customers/{customer_id}/contacts
# LIST CUSTOMER CONTACTS
# ============================================================

@router.get(
    "/{customer_id}/contacts",
    response_model=List[Contact],
    summary="List Customer Contacts",
)
async def list_customer_contacts(
    customer_id: str,
):

    try:

        customer = await find_customer(
            customer_id
        )

        if not customer:

            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found.",
            )

        actual_customer_id = (
            customer.get("customer_id")
            or customer_id
        )

        contacts = await db.contacts.find(
            {
                "customer_id": actual_customer_id
            },
            {
                "_id": 0
            },
        ).sort(
            [
                ("created_at", -1)
            ]
        ).to_list(
            length=1000
        )

        result = []

        for contact in contacts:

            result.append(
                Contact.model_validate(
                    contact
                )
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:

        print(
            f"ERROR: GET customer contacts failed: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to list customer contacts: {str(exc)}",
        )


# ============================================================
# GET /customers/{customer_id}/contacts/{contact_id}
# GET CUSTOMER CONTACT DETAIL
# ============================================================

@router.get(
    "/{customer_id}/contacts/{contact_id}",
    response_model=Contact,
    summary="Get Customer Contact",
)
async def get_customer_contact(
    customer_id: str,
    contact_id: str,
):

    try:

        contact = await find_contact(
            customer_id=customer_id,
            contact_id=contact_id,
        )

        if not contact:

            raise HTTPException(
                status_code=404,
                detail=f"Contact {contact_id} not found.",
            )

        return Contact.model_validate(
            contact
        )

    except HTTPException:
        raise

    except Exception as exc:

        print(
            f"ERROR: GET contact failed: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to get contact: {str(exc)}",
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

        customer = await find_customer(
            customer_id
        )

        if not customer:

            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found.",
            )

        actual_customer_id = (
            customer.get("customer_id")
            or customer_id
        )

        now = utc_now()

        contact_id = (
            f"CON-{now.strftime('%Y%m%d%H%M%S')}"
            f"-{secrets.token_hex(3).upper()}"
        )

        contact = {

            "id": contact_id,

            "contact_id": contact_id,

            "customer_id": actual_customer_id,

            "first_name": payload.first_name,

            "last_name": payload.last_name,

            "position": payload.position,

            "department": payload.department,

            "email": payload.email,

            "mobile": payload.mobile,

            "contact_type": payload.contact_type,

            "is_decision_maker": (
                payload.is_decision_maker
            ),

            "status": payload.status,

            "notes": payload.notes,

            "created_at": now,

            "updated_at": now,
        }

        await db.contacts.insert_one(
            contact
        )

        return Contact.model_validate(
            contact
        )

    except HTTPException:
        raise

    except Exception as exc:

        print(
            f"ERROR: POST customer contact failed: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to create customer contact: {str(exc)}",
        )


# ============================================================
# PUT /customers/{customer_id}/contacts/{contact_id}
# UPDATE CUSTOMER CONTACT
# ============================================================

@router.put(
    "/{customer_id}/contacts/{contact_id}",
    response_model=Contact,
    summary="Update Customer Contact",
)
async def update_customer_contact(
    customer_id: str,
    contact_id: str,
    payload: ContactCreate,
):

    try:

        customer = await find_customer(
            customer_id
        )

        if not customer:

            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found.",
            )

        actual_customer_id = (
            customer.get("customer_id")
            or customer_id
        )

        contact = await db.contacts.find_one(
            {
                "$or": [
                    {
                        "id": contact_id
                    },
                    {
                        "contact_id": contact_id
                    },
                ],
                "customer_id": actual_customer_id,
            }
        )

        if not contact:

            raise HTTPException(
                status_code=404,
                detail=f"Contact {contact_id} not found.",
            )

        update_data = payload.model_dump()

        update_data["updated_at"] = utc_now()

        await db.contacts.update_one(
            {
                "_id": contact["_id"]
            },
            {
                "$set": update_data
            }
        )

        updated = await db.contacts.find_one(
            {
                "_id": contact["_id"]
            },
            {
                "_id": 0
            },
        )

        return Contact.model_validate(
            updated
        )

    except HTTPException:
        raise

    except Exception as exc:

        print(
            f"ERROR: PUT contact failed: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to update contact: {str(exc)}",
        )


# ============================================================
# DELETE /customers/{customer_id}/contacts/{contact_id}
# DELETE CUSTOMER CONTACT
# ============================================================

@router.delete(
    "/{customer_id}/contacts/{contact_id}",
    summary="Delete Customer Contact",
)
async def delete_customer_contact(
    customer_id: str,
    contact_id: str,
):

    try:

        customer = await find_customer(
            customer_id
        )

        if not customer:

            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found.",
            )

        actual_customer_id = (
            customer.get("customer_id")
            or customer_id
        )

        result = await db.contacts.delete_one(
            {
                "$or": [
                    {
                        "id": contact_id
                    },
                    {
                        "contact_id": contact_id
                    },
                ],
                "customer_id": actual_customer_id,
            }
        )

        if result.deleted_count == 0:

            raise HTTPException(
                status_code=404,
                detail=f"Contact {contact_id} not found.",
            )

        return {
            "status": "success",
            "message": "Contact deleted successfully",
            "contact_id": contact_id,
            "customer_id": actual_customer_id,
        }

    except HTTPException:
        raise

    except Exception as exc:

        print(
            f"ERROR: DELETE contact failed: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete contact: {str(exc)}",
        )


# ============================================================
# ROUTER READY
# ============================================================

print(
    "INFO: ✓ routers.customers"
)
