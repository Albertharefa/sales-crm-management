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
# LIST ACTIVITIES
# ============================================================

@router.get("", response_model=Paginated)
async def list_activities(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    status: str | None = None,
    user: dict = Depends(current_user),
):
    filters = {}

    if status:
        filters["status"] = status

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

@router.post("", response_model=Activity)
async def create_activity(
    payload: ActivityCreate,
    user: dict = Depends(current_user),
):
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

        "sales_id": user.get("id"),
        "sales_name": user.get("name"),

        "subject": payload.subject,
        "activity_type": payload.activity_type,
        "date": payload.date,

        "description": payload.description,

        "status": payload.status or "Open",

        "next_follow_up": payload.next_follow_up,

        "created_at": now(),
    }

    await db.activities.insert_one(doc)

    await audit(
        user,
        "Create",
        "Aktivitas",
        doc["id"],
        {
            "subject": doc["subject"],
            "customer_id": doc["customer_id"],
            "activity_type": doc["activity_type"],
        },
    )

    return Activity(**doc)


# ============================================================
# LIST ACTIVITIES BY CUSTOMER
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
    customer = await db.customers.find_one(
        {"id": customer_id}
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer tidak ditemukan",
        )

    skip = (page - 1) * page_size

    total = await db.activities.count_documents(
        {"customer_id": customer_id}
    )

    cursor = (
        db.activities
        .find({"customer_id": customer_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )

    items = []

    async for doc in cursor:
        items.append(Activity(**doc))

    return Paginated(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


# ============================================================
# LIST TASKS
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
)
async def update_task(
    task_id: str,
    status: str,
    user: dict = Depends(current_user),
):
    doc = await db.tasks.find_one(
        {"id": task_id}
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Task tidak ditemukan",
        )

    await db.tasks.update_one(
        {"id": task_id},
        {
            "$set": {
                "status": status,
                "updated_at": now(),
            }
        },
    )

    updated_doc = {
        **doc,
        "status": status,
        "updated_at": now(),
    }

    await audit(
        user,
        "Update",
        "Task",
        task_id,
        {
            "status": status,
        },
    )

    return Task(**updated_doc)
