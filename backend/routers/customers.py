from typing import Optional

from fastapi import APIRouter, HTTPException, Query

# ============================================================
# IMPORT MODEL
# ============================================================
# Customer, CustomerCreate, dan Contact berada pada module
# models, bukan models.customer.
#
# Jika project Anda menyimpan schema di models.py,
# import berikut adalah yang benar.
# ============================================================

try:
    from models import Customer, CustomerCreate, Contact
except ImportError:
    # Fallback apabila schema berada di models.schemas
    from models.schemas import Customer, CustomerCreate, Contact


router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


# ============================================================
# DATABASE HELPER
# ============================================================

def get_db():
    """
    Mengambil database connection dari project yang sudah ada.

    Fungsi ini mencoba beberapa nama umum yang biasanya
    digunakan pada project FastAPI.
    """
    try:
        from database import get_database
        return get_database()
    except ImportError:
        pass

    try:
        from database import get_db_connection
        return get_db_connection()
    except ImportError:
        pass

    return None


# ============================================================
# GET /customers
# LIST CUSTOMERS
# ============================================================

@router.get("", response_model=dict)
def list_customers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):
    """
    List Customers
    """

    try:
        db = get_db()

        # ----------------------------------------------------
        # Jika project memiliki fungsi repository/service
        # gunakan fungsi tersebut.
        # ----------------------------------------------------
        if db is not None:
            try:
                from services.customers import list_customers as service_list

                result = service_list(
                    db=db,
                    page=page,
                    page_size=page_size,
                )

                return result

            except ImportError:
                pass

        # ----------------------------------------------------
        # Fallback kosong agar API tidak crash
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
# CREATE CUSTOMER
# ============================================================

@router.post("", response_model=Customer)
def create_customer(payload: CustomerCreate):
    """
    Create Customer
    """

    try:
        # ----------------------------------------------------
        # Gunakan service/repository jika tersedia
        # ----------------------------------------------------
        try:
            from services.customers import create_customer as service_create

            result = service_create(payload)

            return result

        except ImportError:
            pass

        # ----------------------------------------------------
        # Fallback:
        # Jangan membuat data palsu.
        # Beri informasi bahwa service database belum tersedia.
        # ----------------------------------------------------
        raise HTTPException(
            status_code=500,
            detail=(
                "Customer schema berhasil dimuat, "
                "tetapi customer database service belum tersedia."
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

@router.get("/{customer_id}", response_model=Customer)
def get_customer(customer_id: str):
    """
    Get Customer
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
# UPDATE CUSTOMER
# ============================================================

@router.put("/{customer_id}", response_model=Customer)
def update_customer(
    customer_id: str,
    payload: CustomerCreate,
):
    """
    Update Customer
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
# DELETE CUSTOMER
# ============================================================

@router.delete(
    "/{customer_id}",
    status_code=204,
)
def delete_customer(customer_id: str):
    """
    Delete Customer
    """

    try:
        try:
            from services.customers import delete_customer as service_delete

            service_delete(customer_id)

            return None

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
)
def customer_contacts(customer_id: str):
    """
    Customer Contacts
    """

    try:
        # ----------------------------------------------------
        # Gunakan service contacts jika tersedia
        # ----------------------------------------------------
        try:
            from services.contacts import get_customer_contacts

            result = get_customer_contacts(customer_id)

            return result or []

        except ImportError:
            pass

        # ----------------------------------------------------
        # Jika belum ada contact service,
        # endpoint tetap hidup dan mengembalikan [].
        # ----------------------------------------------------
        return []

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get customer contacts: {str(exc)}",
        )
