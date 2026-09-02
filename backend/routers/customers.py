from datetime import date, datetime
from typing import Optional, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


# ============================================================
# CUSTOMER RESPONSE MODEL
# ============================================================

class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    customer_id: str
    name: str
    company: Optional[str] = None
    industry: str = "Manufacturing"
    city: str = "Jakarta"
    province: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    pic_name: Optional[str] = None
    pic_position: Optional[str] = None
    source: Optional[str] = None
    status: str = "Active"
    sales_id: Optional[str] = None
    sales_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# CUSTOMER CREATE MODEL
# ============================================================

class CustomerCreate(BaseModel):

    name: str = Field(min_length=2)
    industry: str = "Manufacturing"
    source: Optional[str] = None
    city: str = "Jakarta"
    province: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    pic_name: Optional[str] = None
    pic_position: Optional[str] = None
    status: str = "Active"
    sales_id: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_is_none(cls, value):
        if value == "":
            return None
        return value


# ============================================================
# CONTACT RESPONSE MODEL
# ============================================================

class Contact(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    contact_id: str
    customer_id: str
    customer_name: str

    first_name: str
    last_name: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[EmailStr] = None
    mobile: Optional[str] = None

    contact_type: str = "User"
    is_decision_maker: bool = False
    status: str = "Active"

    notes: Optional[str] = None

    created_at: datetime


# ============================================================
# CONTACT CREATE MODEL
# ============================================================

class ContactCreate(BaseModel):

    first_name: str = Field(min_length=1)
    last_name: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None

    email: Optional[EmailStr] = None
    mobile: Optional[str] = None

    contact_type: str = "User"
    is_decision_maker: bool = False
    status: str = "Active"

    notes: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_is_none(cls, value):
        if value == "":
            return None
        return value


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
    response_model=dict,
    summary="List Customers",
)
def list_customers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):

    try:

        # ====================================================
        # COBA SERVICE YANG SUDAH ADA
        # ====================================================

        try:
            from services.customers import list_customers as service_list

            try:
                result = service_list(
                    page=page,
                    page_size=page_size,
                )
            except TypeError:
                result = service_list(
                    page,
                    page_size,
                )

            if result is not None:
                return result

        except ImportError:
            pass

        # ====================================================
        # FALLBACK
        # ====================================================

        return {
            "items": [],
            "page": page,
            "page_size": page_size,
            "total": 0,
        }

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
    response_model=Any,
    summary="Create Customer",
)
def create_customer(
    payload: CustomerCreate,
):

    try:

        # ====================================================
        # GUNAKAN SERVICE CUSTOMER
        # ====================================================

        try:
            from services.customers import create_customer as service_create

            try:
                result = service_create(payload)
            except TypeError:
                result = service_create(
                    payload=payload
                )

            if result is not None:
                return result

        except ImportError:
            pass

        # ====================================================
        # SERVICE BELUM TERSEDIA
        # ====================================================

        raise HTTPException(
            status_code=501,
            detail=(
                "POST /customers sudah aktif, tetapi "
                "services.customers.create_customer belum tersedia."
            ),
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
def get_customer(
    customer_id: str,
):

    try:

        # ====================================================
        # GUNAKAN SERVICE CUSTOMER
        # ====================================================

        try:
            from services.customers import get_customer as service_get

            result = service_get(customer_id)

            if result is None:
                raise HTTPException(
                    status_code=404,
                    detail="Customer not found",
                )

            return result

        except ImportError:
            pass

        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found",
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
    response_model=Any,
    summary="Update Customer",
)
def update_customer(
    customer_id: str,
    payload: CustomerCreate,
):

    try:

        try:
            from services.customers import update_customer as service_update

            try:
                result = service_update(
                    customer_id,
                    payload,
                )
            except TypeError:
                result = service_update(
                    customer_id=customer_id,
                    payload=payload,
                )

            if result is None:
                raise HTTPException(
                    status_code=404,
                    detail="Customer not found",
                )

            return result

        except ImportError:
            pass

        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found",
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
    status_code=204,
    summary="Delete Customer",
)
def delete_customer(
    customer_id: str,
):

    try:

        try:
            from services.customers import delete_customer as service_delete

            result = service_delete(customer_id)

            return result

        except ImportError:
            pass

        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found",
        )

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
    response_model=list[Contact],
    summary="Customer Contacts",
)
def customer_contacts(
    customer_id: str,
):

    try:

        # ====================================================
        # GUNAKAN CONTACT SERVICE
        # ====================================================

        try:
            from services.contacts import get_customer_contacts

            result = get_customer_contacts(customer_id)

            return result or []

        except ImportError:
            pass

        # ====================================================
        # FALLBACK
        # ====================================================

        return []

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
    response_model=Any,
    summary="Create Customer Contact",
)
def create_customer_contact(
    customer_id: str,
    payload: ContactCreate,
):

    try:

        # ====================================================
        # PRIORITAS 1
        # services.contacts.create_customer_contact
        # ====================================================

        try:

            from services.contacts import create_customer_contact as service_create

            try:
                result = service_create(
                    customer_id=customer_id,
                    payload=payload,
                )
            except TypeError:
                result = service_create(
                    customer_id,
                    payload,
                )

            if result is not None:
                return result

        except ImportError:
            pass


        # ====================================================
        # PRIORITAS 2
        # services.contacts.create_contact
        # ====================================================

        try:

            from services.contacts import create_contact as service_create

            try:
                result = service_create(
                    customer_id=customer_id,
                    payload=payload,
                )
            except TypeError:
                result = service_create(
                    customer_id,
                    payload,
                )

            if result is not None:
                return result

        except ImportError:
            pass


        # ====================================================
        # SERVICE BELUM ADA
        # ====================================================

        raise HTTPException(
            status_code=501,
            detail=(
                "POST Contact endpoint sudah aktif, tetapi "
                "service contact untuk menyimpan data belum tersedia."
            ),
        )

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to create customer contact: {str(exc)}",
        )
