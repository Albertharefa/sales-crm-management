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

        from services.contacts import create_customer_contact as service_create

        result = await service_create(
            customer_id=customer_id,
            payload=payload,
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create customer contact: {str(exc)}",
        )
