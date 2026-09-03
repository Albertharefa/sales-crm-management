from fastapi import APIRouter, Depends, HTTPException, Query

from lib.db import db
from models.crm import Activity, ActivityCreate, Paginated, Task
from routers.common import audit, new_id, now, page_collection
from routers.deps import current_user


router = APIRouter(
    prefix="/activities",
    tags=["activities"],
)


# ============================================================
# HELPERS
# ============================================================

async def find_customer(customer_id: str):
    """
    Find customer using public customer_id.
    Fallback to internal id for backward compatibility.
    """

    if not customer_id:
        return None

    customer_id = str(customer_id).strip()

    # Primary: public customer_id
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

    # Fallback: internal id
    customer = await db.customers.find_one(
        {
            "id": customer_id
        },
        {
            "_id": 0
        },
    )

    return customer


# ============================================================
# ACTIVITIES
# ============================================================

@router.get(
    "",
    response_model=Paginated,
)
async def list_activities(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    status: str | None = None,
    customer_id: str | None = None,
    user: dict = Depends(current_user),
):
    """
    List CRM activities.

    Supports:
    - pagination
    - search
    - status filter
    - customer filter
    """

    filters = {}

    if status:
        filters["status"] = status

    if customer_id:
        filters["customer_id"] = customer_id.strip()

    return await page_collection(
        "activities",
        page,
        page_size,
        search,
        filters,
    )


# ============================================================
# CREATE ACTIVITY
# ============================================================

@router.post(
    "",
    response_model=Activity,
)
async def create_activity(
    payload: ActivityCreate,
    user: dict = Depends(current_user),
):
    """
    Create a new CRM activity.
    """

    # --------------------------------------------------------
    # FIND CUSTOMER
    # --------------------------------------------------------

    customer = None

    if payload.customer_id:
        customer = await find_customer(
            payload.customer_id
        )

    # --------------------------------------------------------
    # CUSTOMER INFORMATION
    # --------------------------------------------------------

    customer_name = None
    actual_customer_id = payload.customer_id

    if customer:

        actual_customer_id = customer.get(
            "customer_id",
            payload.customer_id,
        )

        customer_name = (
            customer.get("name")
            or customer.get("company_name")
        )

    # --------------------------------------------------------
    # CREATE ACTIVITY ID
    # --------------------------------------------------------

    activity_id = (
        "ACT-"
        + now().strftime("%Y%m%d")
        + "-"
        + new_id()[:6].upper()
    )

    # --------------------------------------------------------
    # CREATE DOCUMENT
    # --------------------------------------------------------

    doc = {
        "id": new_id(),

        "activity_id": activity_id,

        "customer_id": actual_customer_id,

        "customer_name": customer_name,

        "sales_id": user["id"],

        "sales_name": user["name"],

        **payload.model_dump(mode="json"),

        "created_at": now(),
        "updated_at": now(),
    }

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    await db.activities.insert_one(doc)

    # --------------------------------------------------------
    # AUDIT LOG
    # --------------------------------------------------------

    await audit(
        user,
        "Create",
        "Aktivitas",
        doc["id"],
        {
            "activity_id": activity_id,
            "subject": doc.get("subject"),
            "customer_id": actual_customer_id,
        },
    )

    # --------------------------------------------------------
    # REMOVE MONGODB INTERNAL ID
    # --------------------------------------------------------

    doc.pop("_id", None)

    return Activity(**doc)


# ============================================================
# CUSTOMER ACTIVITIES
# ============================================================

@router.get(
    "/customer/{customer_id}",
    response_model=Paginated,
)
async def list_customer_activities(
    customer_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    user: dict = Depends(current_user),
):
    """
    Get activities for a specific customer.
    """

    customer = await find_customer(customer_id)

    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found",
        )

    actual_customer_id = customer.get(
        "customer_id",
        customer_id,
    )

    return await page_collection(
        "activities",
        page,
        page_size,
        "",
        {
            "customer_id": actual_customer_id
        },
    )


# ============================================================
# TASKS
# ============================================================

@router.get(
    "/tasks",
    response_model=Paginated,
)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    status: str | None = None,
    user: dict = Depends(current_user),
):
    """
    List CRM tasks.
    """

    filters = {}

    if status:
        filters["status"] = status

    return await page_collection(
        "tasks",
        page,
        page_size,
        search,
        filters,
    )


# ============================================================
# UPDATE TASK STATUS
# ============================================================

@router.patch(
    "/tasks/{task_id}",
    response_model=Task,
)
async def update_task(
    task_id: str,
    status: str,
    user: dict = Depends(current_user),
):
    """
    Update task status.
    """

    task = await db.tasks.find_one(
        {
            "id": task_id
        },
        {
            "_id": 0
        },
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task tidak ditemukan",
        )

    updated_at = now()

    await db.tasks.update_one(
        {
            "id": task_id
        },
        {
            "$set": {
                "status": status,
                "updated_at": updated_at,
            }
        },
    )

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    await audit(
        user,
        "Update",
        "Task",
        task_id,
        {
            "old_status": task.get("status"),
            "new_status": status,
        },
    )

    # --------------------------------------------------------
    # RETURN UPDATED TASK
    # --------------------------------------------------------

    task["status"] = status
    task["updated_at"] = updated_at

    return Task(**task)
