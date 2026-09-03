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
    Find customer using either:
    - customer_id
    - id

    This keeps Activities compatible with the existing
    Customers module.
    """

    if not customer_id:
        return None

    customer_id = str(customer_id).strip()

    customer = await db.customers.find_one(
        {"customer_id": customer_id},
        {"_id": 0},
    )

    if customer:
        return customer

    customer = await db.customers.find_one(
        {"id": customer_id},
        {"_id": 0},
    )

    if customer:
        return customer

    return await db.customers.find_one(
        {
            "customer_id": {
                "$regex": f"^{customer_id}$",
                "$options": "i",
            }
        },
        {"_id": 0},
    )


def customer_name(customer: dict | None):
    """
    Safely get customer display name.
    """

    if not customer:
        return None

    return (
        customer.get("name")
        or customer.get("company_name")
        or customer.get("customer_name")
        or ""
    )


# ============================================================
# LIST ACTIVITIES
# ============================================================

@router.get(
    "",
    response_model=Paginated,
    summary="List Activities",
)
async def list_activities(
    page: int = Query(
        1,
        ge=1,
        description="Page number",
    ),
    page_size: int = Query(
        25,
        ge=1,
        le=100,
        description="Number of records per page",
    ),
    search: str = Query(
        "",
        description="Search activities",
    ),
    status: str | None = Query(
        None,
        description="Filter by activity status",
    ),
    activity_type: str | None = Query(
        None,
        description="Filter by activity type",
    ),
    user: dict = Depends(current_user),
):
    """
    Get paginated CRM activities.

    Supports:
    - search
    - status
    - activity_type
    - pagination
    """

    filters = {}

    if status:
        filters["status"] = status

    if activity_type:
        filters["activity_type"] = activity_type

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
    summary="Create Activity",
)
async def create_activity(
    payload: ActivityCreate,
    user: dict = Depends(current_user),
):
    """
    Create a CRM activity.

    The activity is automatically linked to:
    - customer
    - current sales user
    - sales name
    - timestamps
    - activity ID
    """

    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    customer = None

    if payload.customer_id:
        customer = await find_customer(
            payload.customer_id
        )

        if not customer:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Customer "
                    f"{payload.customer_id} "
                    f"not found"
                ),
            )

    # --------------------------------------------------------
    # CUSTOMER ID
    # --------------------------------------------------------

    actual_customer_id = None

    if customer:
        actual_customer_id = (
            customer.get("customer_id")
            or customer.get("id")
            or payload.customer_id
        )

    # --------------------------------------------------------
    # ACTIVITY ID
    # --------------------------------------------------------

    activity_id = (
        "ACT-"
        + now().strftime("%Y%m%d")
        + "-"
        + new_id()[:6].upper()
    )

    # --------------------------------------------------------
    # TIMESTAMP
    # --------------------------------------------------------

    created_at = now()

    # --------------------------------------------------------
    # PAYLOAD
    # --------------------------------------------------------

    payload_data = payload.model_dump(
        mode="json"
    )

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    doc = {
        "id": new_id(),

        "activity_id": activity_id,

        "customer_id": actual_customer_id,

        "customer_name": customer_name(
            customer
        ),

        "sales_id": user.get("id"),

        "sales_name": user.get("name"),

        **payload_data,

        "created_at": created_at,

        "updated_at": created_at,
    }

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    await db.activities.insert_one(doc)

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    await audit(
        user,
        "Create",
        "Aktivitas",
        doc["id"],
        {
            "activity_id": doc["activity_id"],
            "subject": doc.get("subject"),
            "customer_id": doc.get(
                "customer_id"
            ),
        },
    )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    doc.pop("_id", None)

    return Activity(**doc)


# ============================================================
# CUSTOMER ACTIVITIES
# ============================================================

@router.get(
    "/customer/{customer_id}",
    response_model=Paginated,
    summary="List Customer Activities",
)
async def list_customer_activities(
    customer_id: str,
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        25,
        ge=1,
        le=100,
    ),
    user: dict = Depends(current_user),
):
    """
    Get all activities belonging to one customer.
    """

    customer = await find_customer(
        customer_id
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Customer "
                f"{customer_id} "
                f"not found"
            ),
        )

    actual_customer_id = (
        customer.get("customer_id")
        or customer.get("id")
        or customer_id
    )

    total = await db.activities.count_documents(
        {
            "customer_id": actual_customer_id
        }
    )

    skip = (
        (page - 1)
        * page_size
    )

    items = await db.activities.find(
        {
            "customer_id": actual_customer_id
        },
        {
            "_id": 0
        },
    ).sort(
        "created_at",
        -1,
    ).skip(
        skip
    ).limit(
        page_size
    ).to_list(
        page_size
    )

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


# ============================================================
# TASK LIST
# ============================================================

@router.get(
    "/tasks",
    response_model=Paginated,
    summary="List Tasks",
)
async def list_tasks(
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        25,
        ge=1,
        le=100,
    ),
    search: str = Query(
        "",
        description="Search tasks",
    ),
    status: str | None = Query(
        None,
        description="Filter by task status",
    ),
    user: dict = Depends(current_user),
):
    """
    Get CRM tasks with pagination.
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
# UPDATE TASK
# ============================================================

@router.patch(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update Task",
)
async def update_task(
    task_id: str,
    status: str = Query(
        ...,
        description=(
            "Task status, "
            "for example Open, "
            "In Progress, Completed"
        ),
    ),
    user: dict = Depends(current_user),
):
    """
    Update task status.
    """

    task = await db.tasks.find_one(
        {
            "$or": [
                {"id": task_id},
                {"task_id": task_id},
            ]
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
            "$or": [
                {"id": task_id},
                {"task_id": task_id},
            ]
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
        task.get("id", task_id),
        {
            "task_id": task.get(
                "task_id",
                task_id,
            ),
            "status": status,
        },
    )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    task["status"] = status
    task["updated_at"] = updated_at

    return Task(**task)
