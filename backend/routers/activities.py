from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query

from lib.db import db
from models.crm import Activity, ActivityCreate, Paginated, Task
from routers.common import audit, new_id, now
from routers.deps import current_user
from services.sales import get_sales_options


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
    activity_filter: str | None = None,
    activity_type: str | None = None,
    status: str | None = None,
    sales_id: str | None = None,
    user: dict = Depends(current_user),
):
    query: dict = {}

    if search.strip():
        query["$or"] = [
            {"subject": {"$regex": search.strip(), "$options": "i"}},
            {"customer_name": {"$regex": search.strip(), "$options": "i"}},
            {"sales_name": {"$regex": search.strip(), "$options": "i"}},
            {"activity_id": {"$regex": search.strip(), "$options": "i"}},
        ]

    if activity_type:
        query["activity_type"] = activity_type

    if status:
        query["status"] = status

    if sales_id:
        query["sales_id"] = sales_id

    today = date.today().isoformat()

    if activity_filter == "today":
        query["date"] = today
    elif activity_filter == "upcoming":
        query["next_follow_up"] = {"$gte": today}
        query["status"] = status or "Open"
    elif activity_filter == "overdue":
        query["next_follow_up"] = {"$lt": today}
        query["status"] = status or "Open"
    elif activity_filter == "completed":
        query["status"] = "Completed"

    total = await db.activities.count_documents(query)

    cursor = (
        db.activities
        .find(query, {"_id": 0})
        .sort([("date", -1), ("created_at", -1)])
        .skip((page - 1) * page_size)
        .limit(page_size)
    )

    items = await cursor.to_list(page_size)

    return Paginated(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


# ============================================================
# ACTIVITY SUMMARY
# ============================================================

@router.get("/summary")
async def activity_summary(
    user: dict = Depends(current_user),
):
    today = date.today().isoformat()

    today_count = await db.activities.count_documents({"date": today})
    upcoming_count = await db.activities.count_documents({
        "next_follow_up": {"$gte": today},
        "status": "Open",
    })
    overdue_count = await db.activities.count_documents({
        "next_follow_up": {"$lt": today},
        "status": "Open",
    })
    completed_count = await db.activities.count_documents({
        "status": "Completed",
    })

    return {
        "today": today_count,
        "upcoming": upcoming_count,
        "overdue": overdue_count,
        "completed": completed_count,
    }


# ============================================================
# SALES OPTIONS
# ============================================================

@router.get("/sales-options")
async def activity_sales_options(
    user: dict = Depends(current_user),
):
    # Uses the same centralized Users-based Sales master as Customers
    # and Sales Pipeline, keeping all Sales dropdowns synchronized.
    return await get_sales_options()


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
        doc.pop("_id", None)
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

    query: dict = filters.copy()

    if search.strip():
        query["$or"] = [
            {"title": {"$regex": search.strip(), "$options": "i"}},
            {"customer_name": {"$regex": search.strip(), "$options": "i"}},
            {"assigned_user": {"$regex": search.strip(), "$options": "i"}},
        ]

    total = await db.tasks.count_documents(query)

    items = await (
        db.tasks
        .find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list(page_size)
    )

    return Paginated(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
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

    updated_at = now()

    await db.tasks.update_one(
        {"id": task_id},
        {
            "$set": {
                "status": status,
                "updated_at": updated_at,
            }
        },
    )

    updated_doc = {
        **doc,
        "status": status,
        "updated_at": updated_at,
    }
    updated_doc.pop("_id", None)

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
