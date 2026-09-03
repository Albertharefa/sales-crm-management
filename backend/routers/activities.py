from fastapi import APIRouter, Depends, HTTPException, Query

from lib.db import db
from models.crm import (
    Activity,
    ActivityCreate,
    ActivityUpdate,
    Paginated,
    Task,
    TaskUpdate,
)
from routers.common import audit, new_id, now, page_collection
from routers.deps import current_user


router = APIRouter(
    prefix="/activities",
    tags=["activities"],
)


# ============================================================
# ACTIVITIES - LIST
# ============================================================

@router.get(
    "",
    response_model=Paginated,
    summary="List Activities",
)
async def list_activities(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    status: str | None = None,
    activity_type: str | None = None,
    customer_id: str | None = None,
    user: dict = Depends(current_user),
):
    """
    List CRM activities with pagination and filters.
    """

    filters = {}

    if status:
        filters["status"] = status

    if activity_type:
        filters["activity_type"] = activity_type

    if customer_id:
        filters["customer_id"] = customer_id

    return await page_collection(
        "activities",
        page,
        page_size,
        search,
        filters,
    )


# ============================================================
# ACTIVITIES - CREATE
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
    Create a new CRM activity.
    """

    customer = None

    if payload.customer_id:
        customer = await db.customers.find_one(
            {"id": payload.customer_id}
        )

        if not customer:
            raise HTTPException(
                status_code=404,
                detail="Customer tidak ditemukan",
            )

    activity_id = new_id()

    doc = {
        "id": activity_id,

        "activity_id": new_id()[:8].upper(),

        "customer_id": payload.customer_id,

        "customer_name": (
            customer.get("name")
            if customer
            else None
        ),

        "sales_id": user["id"],

        "sales_name": user["name"],

        **payload.model_dump(mode="json"),

        "created_at": now(),
    }

    await db.activities.insert_one(doc)

    await audit(
        user,
        "Create",
        "Aktivitas",
        doc["id"],
        {
            "subject": doc.get("subject"),
            "customer_id": doc.get("customer_id"),
            "activity_type": doc.get("activity_type"),
        },
    )

    return Activity(**doc)


# ============================================================
# ACTIVITIES - UPDATE
# ============================================================

@router.patch(
    "/{activity_id}",
    response_model=Activity,
    summary="Update Activity",
)
async def update_activity(
    activity_id: str,
    payload: ActivityUpdate,
    user: dict = Depends(current_user),
):
    """
    Update an existing activity.
    """

    existing = await db.activities.find_one(
        {"id": activity_id}
    )

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Aktivitas tidak ditemukan",
        )

    update_data = payload.model_dump(
        exclude_unset=True,
        mode="json",
    )

    if "customer_id" in update_data:

        customer_id = update_data["customer_id"]

        customer = None

        if customer_id:
            customer = await db.customers.find_one(
                {"id": customer_id}
            )

            if not customer:
                raise HTTPException(
                    status_code=404,
                    detail="Customer tidak ditemukan",
                )

            update_data["customer_name"] = customer.get(
                "name"
            )

        else:
            update_data["customer_name"] = None

    update_data["updated_at"] = now()

    await db.activities.update_one(
        {"id": activity_id},
        {"$set": update_data},
    )

    updated = {
        **existing,
        **update_data,
    }

    await audit(
        user,
        "Update",
        "Aktivitas",
        activity_id,
        {
            "subject": updated.get("subject"),
        },
    )

    return Activity(**updated)


# ============================================================
# ACTIVITIES - CUSTOMER
# ============================================================

@router.get(
    "/customer/{customer_id}",
    response_model=Paginated,
    summary="List Customer Activities",
)
async def list_customer_activities(
    customer_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    user: dict = Depends(current_user),
):
    """
    Get all activities belonging to one customer.
    """

    customer = await db.customers.find_one(
        {"id": customer_id}
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    return await page_collection(
        "activities",
        page,
        page_size,
        search,
        {
            "customer_id": customer_id,
        },
    )


# ============================================================
# TASKS - LIST
# ============================================================

@router.get(
    "/tasks",
    response_model=Paginated,
    summary="List Tasks",
)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    status: str | None = None,
    priority: str | None = None,
    user: dict = Depends(current_user),
):
    """
    List CRM tasks.
    """

    filters = {}

    if status:
        filters["status"] = status

    if priority:
        filters["priority"] = priority

    return await page_collection(
        "tasks",
        page,
        page_size,
        search,
        filters,
    )


# ============================================================
# TASKS - UPDATE STATUS
# ============================================================

@router.patch(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update Task",
)
async def update_task(
    task_id: str,
    status: str | None = None,
    payload: TaskUpdate | None = None,
    user: dict = Depends(current_user),
):
    """
    Update task status or other task fields.

    Backward compatible:
    PATCH /activities/tasks/{task_id}?status=Completed

    Also supports JSON body:
    {
        "status": "Completed"
    }
    """

    doc = await db.tasks.find_one(
        {"id": task_id}
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Task tidak ditemukan",
        )

    update_data = {}

    # --------------------------------------------------------
    # JSON BODY
    # --------------------------------------------------------

    if payload is not None:

        update_data = payload.model_dump(
            exclude_unset=True,
            mode="json",
        )

    # --------------------------------------------------------
    # QUERY PARAMETER STATUS
    # --------------------------------------------------------

    if status is not None:
        update_data["status"] = status

    # --------------------------------------------------------
    # NO DATA
    # --------------------------------------------------------

    if not update_data:

        return Task(**doc)

    update_data["updated_at"] = now()

    await db.tasks.update_one(
        {"id": task_id},
        {
            "$set": update_data
        },
    )

    updated = {
        **doc,
        **update_data,
    }

    await audit(
        user,
        "Update",
        "Task",
        task_id,
        {
            "status": updated.get("status"),
            "title": updated.get("title"),
        },
    )

    return Task(**updated)
