from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from lib.db import db
from models.crm import Activity, ActivityCreate, ActivityUpdate, Paginated, Task
from routers.common import audit, new_id, now
from routers.deps import current_user
from services.sales import get_sales_options
from routers.customers import ensure_customer_access, customer_scope_query


router = APIRouter(
    prefix="/activities",
    tags=["activities"],
)

ACTIVITY_TYPES = {
    "Call",
    "WhatsApp",
    "Email",
    "Meeting",
    "Visit",
    "Presentation",
    "Follow Up",
    "Other",
}
ACTIVITY_STATUSES = {"Open", "Completed", "Cancelled"}
TASK_STATUSES = {"Pending", "In Progress", "Completed", "Cancelled"}


async def visible_activity_sales_ids(user: dict) -> list[str]:
    """Return activity owner IDs visible to the current user."""
    role = str(user.get("role") or "").upper()
    current_id = str(user.get("id") or "")

    if role == "SUPER_ADMIN":
        users = await db.users.find(
            {
                "role": "SALES",
                "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]},
            },
            {"_id": 0, "id": 1},
        ).to_list(1000)
        return [str(item["id"]) for item in users if item.get("id")]

    if role == "SALES_MANAGER":
        users = await db.users.find(
            {
                "$or": [
                    {"id": current_id},
                    {"manager_id": current_id, "role": "SALES"},
                ],
                "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]},
            },
            {"_id": 0, "id": 1},
        ).to_list(1000)
        return [str(item["id"]) for item in users if item.get("id")]

    if role == "SALES" and current_id:
        return [current_id]

    return []


async def ensure_activity_access(doc: dict, user: dict) -> None:
    """Prevent users from viewing or changing activities outside their scope."""
    visible_ids = await visible_activity_sales_ids(user)
    sales_id = str(doc.get("sales_id") or "")
    if sales_id not in visible_ids:
        raise HTTPException(
            status_code=403,
            detail="Anda tidak memiliki akses ke aktivitas ini",
        )


async def visible_task_assignees(user: dict) -> list[str]:
    """Return assigned-user names visible to the current user."""
    role = str(user.get("role") or "").upper()
    current_name = str(user.get("name") or "").strip()

    if role == "SUPER_ADMIN":
        return []

    if role == "SALES":
        return [current_name] if current_name else []

    if role == "SALES_MANAGER":
        names = [current_name] if current_name else []
        reports = await db.users.find(
            {
                "manager_id": user.get("id"),
                "role": "SALES",
                "status": {"$nin": ["INACTIVE", "DISABLED", "Inactive", "Disabled"]},
            },
            {"_id": 0, "name": 1},
        ).to_list(1000)
        names.extend(str(item["name"]).strip() for item in reports if item.get("name"))
        return list(dict.fromkeys(names))

    return []


async def ensure_task_access(doc: dict, user: dict) -> None:
    role = str(user.get("role") or "").upper()
    if role == "SUPER_ADMIN":
        return

    assigned = str(doc.get("assigned_user") or "").strip()
    allowed = await visible_task_assignees(user)
    if assigned not in allowed:
        raise HTTPException(
            status_code=403,
            detail="Anda tidak memiliki akses ke task ini",
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
    if activity_type and activity_type not in ACTIVITY_TYPES:
        raise HTTPException(status_code=422, detail="Tipe aktivitas tidak valid")
    if status and status not in ACTIVITY_STATUSES:
        raise HTTPException(status_code=422, detail="Status aktivitas tidak valid")
    if activity_filter and activity_filter not in {"today", "upcoming", "overdue", "completed"}:
        raise HTTPException(status_code=422, detail="Filter aktivitas tidak valid")

    visible_ids = await visible_activity_sales_ids(user)
    query: dict = {"sales_id": {"$in": visible_ids}}

    if sales_id:
        if sales_id not in visible_ids:
            raise HTTPException(status_code=403, detail="Sales tersebut berada di luar scope Anda")
        query["sales_id"] = sales_id

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
    items = await (
        db.activities
        .find(query, {"_id": 0})
        .sort([("date", -1), ("created_at", -1)])
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list(page_size)
    )

    return Paginated(items=items, page=page, page_size=page_size, total=total)


# ============================================================
# ACTIVITY SUMMARY
# ============================================================

@router.get("/summary")
async def activity_summary(user: dict = Depends(current_user)):
    today = date.today().isoformat()
    visible_ids = await visible_activity_sales_ids(user)
    scope = {"sales_id": {"$in": visible_ids}}

    today_count = await db.activities.count_documents({**scope, "date": today})
    upcoming_count = await db.activities.count_documents({
        **scope,
        "next_follow_up": {"$gte": today},
        "status": "Open",
    })
    overdue_count = await db.activities.count_documents({
        **scope,
        "next_follow_up": {"$lt": today},
        "status": "Open",
    })
    completed_count = await db.activities.count_documents({
        **scope,
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
async def activity_sales_options(user: dict = Depends(current_user)):
    visible_ids = await visible_activity_sales_ids(user)
    options = await get_sales_options()
    return [item for item in options if str(item.get("id") or "") in visible_ids]


@router.get("/customer-options")
async def activity_customer_options(user: dict = Depends(current_user)):
    """Return the live Customer master for the activity form."""
    scope = await customer_scope_query(user)
    customers = await db.customers.find(
        scope,
        {"_id": 0, "id": 1, "customer_id": 1, "name": 1, "company_name": 1},
    ).sort("name", 1).to_list(1000)

    result = []
    seen_ids = set()
    for customer in customers:
        customer_id = customer.get("id") or customer.get("customer_id")
        if not customer_id or customer_id in seen_ids:
            continue
        display_name = (
            customer.get("name")
            or customer.get("company_name")
            or customer.get("customer_id")
            or str(customer_id)
        )
        result.append({"id": str(customer_id), "name": str(display_name)})
        seen_ids.add(customer_id)
    return result


# ============================================================
# CREATE ACTIVITY
# ============================================================

@router.post("", response_model=Activity)
async def create_activity(payload: ActivityCreate, user: dict = Depends(current_user)):
    if payload.activity_type not in ACTIVITY_TYPES:
        raise HTTPException(status_code=422, detail="Tipe aktivitas tidak valid")
    if payload.status not in ACTIVITY_STATUSES:
        raise HTTPException(status_code=422, detail="Status aktivitas tidak valid")

    customer = None
    if payload.customer_id:
        customer = await db.customers.find_one({"id": payload.customer_id})
        if not customer:
            customer = await db.customers.find_one({"customer_id": payload.customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
        await ensure_customer_access(customer, user)

    role = str(user.get("role") or "").upper()
    if role not in {"SUPER_ADMIN", "SALES_MANAGER", "SALES"}:
        raise HTTPException(status_code=403, detail="Role Anda tidak memiliki akses ke Aktivitas Sales")

    opportunity = None
    if payload.opportunity_id:
        opportunity = await db.opportunities.find_one({"id": payload.opportunity_id})
        if not opportunity:
            opportunity = await db.opportunities.find_one({"opportunity_id": payload.opportunity_id})
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity tidak ditemukan")
        await ensure_activity_access(opportunity, user)
        opportunity_customer = str(opportunity.get("customer_id") or "")
        canonical_customer = str((customer or {}).get("id") or payload.customer_id or "")
        if opportunity_customer and canonical_customer and opportunity_customer != canonical_customer:
            linked = await db.customers.find_one({"id": opportunity_customer})
            linked_id = str((linked or {}).get("id") or opportunity_customer)
            if linked_id != canonical_customer:
                raise HTTPException(status_code=409, detail="Opportunity tidak terkait dengan Customer yang dipilih")

    activity_id = new_id()
    doc = {
        "id": activity_id,
        "activity_id": new_id()[:8].upper(),
        "customer_id": (customer or {}).get("id") if customer else payload.customer_id,
        "opportunity_id": (opportunity or {}).get("id") if opportunity else payload.opportunity_id,
        "customer_name": (customer or {}).get("name") if customer else None,
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

@router.get("/customer/{customer_id}", response_model=Paginated)
async def list_customer_activities(
    customer_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    user: dict = Depends(current_user),
):
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        customer = await db.customers.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    await ensure_customer_access(customer, user)

    visible_ids = await visible_activity_sales_ids(user)
    query = {"customer_id": customer.get("id") or customer_id, "sales_id": {"$in": visible_ids}}
    skip = (page - 1) * page_size
    total = await db.activities.count_documents(query)
    items = await (
        db.activities
        .find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
        .to_list(page_size)
    )

    return Paginated(items=items, page=page, page_size=page_size, total=total)


# ============================================================
# LIST TASKS
# ============================================================

@router.get("/tasks", response_model=Paginated)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str = "",
    status: str | None = None,
    user: dict = Depends(current_user),
):
    if status and status not in TASK_STATUSES:
        raise HTTPException(status_code=422, detail="Status task tidak valid")

    role = str(user.get("role") or "").upper()
    if role == "SUPER_ADMIN":
        query: dict = {}
    else:
        allowed = await visible_task_assignees(user)
        query = {"assigned_user": {"$in": allowed}}

    if status:
        query["status"] = status
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
    return Paginated(items=items, page=page, page_size=page_size, total=total)


# ============================================================
# UPDATE TASK
# ============================================================

@router.patch("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    status: str,
    user: dict = Depends(current_user),
):
    if status not in TASK_STATUSES:
        raise HTTPException(status_code=422, detail="Status task tidak valid")

    doc = await db.tasks.find_one({"id": task_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Task tidak ditemukan")
    await ensure_task_access(doc, user)

    updated_at = now()
    await db.tasks.update_one(
        {"id": task_id},
        {"$set": {"status": status, "updated_at": updated_at}},
    )
    updated_doc = {**doc, "status": status, "updated_at": updated_at}
    updated_doc.pop("_id", None)

    await audit(user, "Update", "Task", task_id, {"status": status})
    return Task(**updated_doc)


# ============================================================
# ACTIVITY DETAIL
# ============================================================

@router.get("/{activity_id}", response_model=Activity)
async def get_activity(activity_id: str, user: dict = Depends(current_user)):
    doc = await db.activities.find_one({"id": activity_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Aktivitas tidak ditemukan")
    await ensure_activity_access(doc, user)
    return Activity(**doc)


# ============================================================
# UPDATE ACTIVITY
# ============================================================

@router.put("/{activity_id}", response_model=Activity)
async def update_activity(
    activity_id: str,
    payload: ActivityUpdate,
    user: dict = Depends(current_user),
):
    doc = await db.activities.find_one({"id": activity_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Aktivitas tidak ditemukan")
    await ensure_activity_access(doc, user)

    update_data = payload.model_dump(exclude_unset=True)
    if "activity_type" in update_data and update_data["activity_type"] not in ACTIVITY_TYPES:
        raise HTTPException(status_code=422, detail="Tipe aktivitas tidak valid")
    if "status" in update_data and update_data["status"] not in ACTIVITY_STATUSES:
        raise HTTPException(status_code=422, detail="Status aktivitas tidak valid")

    if not update_data:
        doc.pop("_id", None)
        return Activity(**doc)

    updated_at = now()
    update_data["updated_at"] = updated_at
    await db.activities.update_one({"id": activity_id}, {"$set": update_data})

    updated_doc = {**doc, **update_data}
    updated_doc.pop("_id", None)
    await audit(
        user,
        "Update",
        "Aktivitas",
        activity_id,
        {
            "subject": updated_doc.get("subject"),
            "activity_type": updated_doc.get("activity_type"),
            "status": updated_doc.get("status"),
        },
    )
    return Activity(**updated_doc)


# ============================================================
# DELETE ACTIVITY
# ============================================================

@router.delete("/{activity_id}")
async def delete_activity(activity_id: str, user: dict = Depends(current_user)):
    doc = await db.activities.find_one({"id": activity_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Aktivitas tidak ditemukan")
    await ensure_activity_access(doc, user)

    await db.activities.delete_one({"id": activity_id})
    await audit(
        user,
        "Delete",
        "Aktivitas",
        activity_id,
        {
            "subject": doc.get("subject"),
            "activity_type": doc.get("activity_type"),
        },
    )
    return {"message": "Aktivitas berhasil dihapus"}
