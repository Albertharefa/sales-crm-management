from typing import Optional

from fastapi import APIRouter, HTTPException, Query

# ============================================================
# CUSTOMER ROUTER
# ============================================================
#
# PENTING:
# Jangan menggunakan:
#     from models.customer import ...
#
# Schema Customer, CustomerCreate, dan Contact diambil
# langsung dari module models.
# ============================================================

from models import Customer, CustomerCreate, Contact


router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


# ============================================================
# DATABASE / SERVICE HELPER
# ============================================================

def get_customer_service():
    """
    Mengambil customer service jika tersedia.
    """

    try:
        from services.customers import (
            list_customers,
            create_customer,
            get_customer,
            update_customer,
            delete_customer,
        )

        return {
            "list": list_customers,
            "create": create_customer,
            "get": get_customer,
            "update": update_customer,
            "delete": delete_customer,
        }

    except ImportError:
        return None


# ============================================================
# GET /customers
# LIST CUSTOMERS
# ============================================================

@router.get("", response_model=dict)
def list_customers_endpoint(
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
    """
    List Customers
    """

    service = get_customer_service()

    if service is None:
        return {
            "items": [],
            "page": page,
            "page_size": page_size,
            "total": 0,
        }

    try:
        result = service["list"](
            page=page,
            page_size=page_size,
        )

        return result

    except TypeError:
        try:
            result = service["list"](
                page,
                page_size,
            )

            return result

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list customers: {str(exc)}",
            )

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
)
def create_customer_endpoint(
    payload: CustomerCreate,
):
    """
    Create Customer
    """

    service = get_customer_service()

    if service is None:
        raise HTTPException(
            status_code=500,
            detail="Customer service is not available.",
        )

    try:
        result = service["create"](payload)

        return result

    except TypeError:
        try:
            result = service["create"](
                payload=payload
            )

            return result

        except HTTPException:
            raise

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create customer: {str(exc)}",
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
)
def get_customer_endpoint(
    customer_id: str,
):
    """
    Get Customer
    """

    service = get_customer_service()

    if service is None:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found",
        )

    try:
        result = service["get"](customer_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found",
            )

        return result

    except HTTPException:
        raise

    except TypeError:
        try:
            result = service["get"](
                customer_id=customer_id
            )

            if result is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Customer {customer_id} not found",
                )

            return result

        except HTTPException:
            raise

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get customer: {str(exc)}",
            )

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
)
def update_customer_endpoint(
    customer_id: str,
    payload: CustomerCreate,
):
    """
    Update Customer
    """

    service = get_customer_service()

    if service is None:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found",
        )

    try:
        result = service["update"](
            customer_id,
            payload,
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found",
            )

        return result

    except HTTPException:
        raise

    except TypeError:
        try:
            result = service["update"](
                customer_id=customer_id,
                payload=payload,
            )

            if result is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Customer {customer_id} not found",
                )

            return result

        except HTTPException:
            raise

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update customer: {str(exc)}",
            )

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
def delete_customer_endpoint(
    customer_id: str,
):
    """
    Delete Customer
    """

    service = get_customer_service()

    if service is None:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found",
        )

    try:
        service["delete"](customer_id)

        return None

    except HTTPException:
        raise

    except TypeError:
        try:
            service["delete"](
                customer_id=customer_id
            )

            return None

        except HTTPException:
            raise

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete customer: {str(exc)}",
            )

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
def customer_contacts(
    customer_id: str,
):
    """
    Customer Contacts
    """

    try:
        from services.contacts import get_customer_contacts

    except ImportError:
        # Contact service belum tersedia.
        # Endpoint tetap valid dan mengembalikan list kosong.
        return []

    try:
        result = get_customer_contacts(
            customer_id
        )

        return result or []

    except TypeError:
        try:
            result = get_customer_contacts(
                customer_id=customer_id
            )

            return result or []

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get customer contacts: {str(exc)}",
            )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get customer contacts: {str(exc)}",
        )
