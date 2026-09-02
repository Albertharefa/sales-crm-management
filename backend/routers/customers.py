from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================
# MODEL IMPORT
# ============================================================
# Jangan menggunakan:
# from models.customer import ...
#
# Karena project Anda menggunakan models.py / models package.
# Kita coba beberapa struktur yang umum tanpa membuat server
# crash apabila salah satu struktur tidak tersedia.
# ============================================================

try:
    from models import Customer, CustomerCreate, Contact

except ImportError:

    try:
        from models.schemas import Customer, CustomerCreate, Contact

    except ImportError:

        try:
            from models.models import Customer, CustomerCreate, Contact

        except ImportError as exc:
            raise ImportError(
                "Customer models tidak ditemukan. "
                "Pastikan Customer, CustomerCreate dan Contact "
                "berada di models.py atau models.schemas."
            ) from exc


# ============================================================
# CONTACT CREATE
# ============================================================
# ContactCreate belum ada pada models yang Anda kirim.
# Karena itu kita definisikan di router ini agar endpoint
# POST /customers/{customer_id}/contacts bisa langsung muncul
# di Swagger.
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
        return None if value == "" else value


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


# ============================================================
# GET /customers
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
    """
    Menampilkan daftar customer.
    """

    try:

        # ----------------------------------------------------
        # Gunakan service jika tersedia
        # ----------------------------------------------------
        try:
            from services.customers import list_customers as service_list

            result = service_list(
                page=page,
                page_size=page_size,
            )

            return result

        except ImportError:
            pass

        # ----------------------------------------------------
        # Fallback aman
        # ----------------------------------------------------
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
# ============================================================

@router.post(
    "",
    response_model=Customer,
    summary="Create Customer",
)
def create_customer(
    payload: CustomerCreate,
):
    """
    Membuat customer baru.
    """

    try:

        # ----------------------------------------------------
        # Gunakan service yang sudah ada
        # ----------------------------------------------------
        try:
            from services.customers import create_customer as service_create

            result = service_create(payload)

            return result

        except ImportError:
            pass

        # ----------------------------------------------------
        # Jika service belum tersedia
        # ----------------------------------------------------
        raise HTTPException(
            status_code=501,
            detail=(
                "Customer endpoint sudah aktif, tetapi "
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
# ============================================================

@router.get(
    "/{customer_id}",
    response_model=Customer,
    summary="Get Customer",
)
def get_customer(
    customer_id: str,
):
    """
    Mengambil detail satu customer.
    """

    try:

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
# ============================================================

@router.put(
    "/{customer_id}",
    response_model=Customer,
    summary="Update Customer",
)
def update_customer(
    customer_id: str,
    payload: CustomerCreate,
):
    """
    Mengupdate customer.
    """

    try:

        try:
            from services.customers import update_customer as service_update

            result = service_update(
                customer_id,
                payload,
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
# ============================================================

@router.delete(
    "/{customer_id}",
    status_code=204,
    summary="Delete Customer",
)
def delete_customer(
    customer_id: str,
):
    """
    Menghapus customer.
    """

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
# ============================================================

@router.get(
    "/{customer_id}/contacts",
    response_model=list[Contact],
    summary="Customer Contacts",
)
def customer_contacts(
    customer_id: str,
):
    """
    Menampilkan semua contact milik customer.
    """

    try:

        # ----------------------------------------------------
        # Gunakan contact service jika tersedia
        # ----------------------------------------------------
        try:
            from services.contacts import get_customer_contacts

            result = get_customer_contacts(customer_id)

            return result or []

        except ImportError:
            pass

        # ----------------------------------------------------
        # Jika service belum ada, endpoint tetap hidup.
        # ----------------------------------------------------
        return []

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to get customer contacts: {str(exc)}",
        )


# ============================================================
# POST /customers/{customer_id}/contacts
# ============================================================

@router.post(
    "/{customer_id}/contacts",
    response_model=Contact,
    summary="Create Customer Contact",
)
def create_customer_contact(
    customer_id: str,
    payload: ContactCreate,
):
    """
    Membuat contact baru untuk customer tertentu.
    """

    try:

        # ----------------------------------------------------
        # Gunakan contact service jika tersedia
        # ----------------------------------------------------
        try:
            from services.contacts import create_customer_contact as service_create

            result = service_create(
                customer_id=customer_id,
                payload=payload,
            )

            if result is None:
                raise HTTPException(
                    status_code=500,
                    detail="Contact service returned no result.",
                )

            return result

        except ImportError:
            pass

        # ----------------------------------------------------
        # Coba nama fungsi service alternatif
        # ----------------------------------------------------
        try:
            from services.contacts import create_contact as service_create

            result = service_create(
                customer_id,
                payload,
            )

            if result is None:
                raise HTTPException(
                    status_code=500,
                    detail="Contact service returned no result.",
                )

            return result

        except ImportError:
            pass

        # ----------------------------------------------------
        # Service belum tersedia
        # ----------------------------------------------------
        raise HTTPException(
            status_code=501,
            detail=(
                "POST Contact endpoint sudah aktif, tetapi "
                "services.contacts.create_customer_contact "
                "atau services.contacts.create_contact "
                "belum tersedia."
            ),
        )

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to create customer contact: {str(exc)}",
        )
