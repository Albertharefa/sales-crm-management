from fastapi import APIRouter, Depends, Query
from lib.db import db
from models.crm import Activity, ActivityCreate, Paginated, Task
from routers.common import audit, new_id, now, page_collection
from routers.deps import current_user

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=Paginated)
async def list_activities(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", status: str | None = None, user: dict = Depends(current_user)):
    return await page_collection("activities", page, page_size, search, {"status": status} if status else {})


@router.post("", response_model=Activity)
async def create_activity(payload: ActivityCreate, user: dict = Depends(current_user)):
    customer = await db.customers.find_one({"id": payload.customer_id}) if payload.customer_id else None
    doc = {"id": new_id(), "activity_id": new_id()[:8].upper(), "customer_name": customer["name"] if customer else None, "sales_id": user["id"], "sales_name": user["name"], **payload.model_dump(mode="json"), "created_at": now()}
    await db.activities.insert_one(doc)
    await audit(user, "Create", "Aktivitas", doc["id"], {"subject": doc["subject"]})
    return Activity(**doc)


@router.get("/tasks", response_model=Paginated)
async def list_tasks(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", user: dict = Depends(current_user)):
    return await page_collection("tasks", page, page_size, search)


@router.patch("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, status: str, user: dict = Depends(current_user)):
    doc = await db.tasks.find_one({"id": task_id})
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task tidak ditemukan")
    await db.tasks.update_one({"id": task_id}, {"$set": {"status": status}})
    return Task(**{**doc, "status": status})