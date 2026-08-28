from fastapi import APIRouter, Depends, HTTPException, Query
from lib.db import db
from models.crm import Opportunity, OpportunityCreate, Paginated
from routers.common import audit, new_id, now, page_collection
from routers.deps import current_user

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
STAGES = ["Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"]


@router.get("", response_model=Paginated)
async def list_opportunities(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), search: str = "", stage: str | None = None, user: dict = Depends(current_user)):
    return await page_collection("opportunities", page, page_size, search, {"stage": stage} if stage else {})


@router.get("/kanban")
async def kanban(user: dict = Depends(current_user)):
    result = []
    for stage in STAGES:
        items = await db.opportunities.find({"stage": stage}).sort("created_at", -1).to_list(100)
        for item in items:
            item.pop("_id", None)
        result.append({"stage": stage, "count": len(items), "value": sum(i.get("value", 0) for i in items), "items": items})
    return result


@router.post("", response_model=Opportunity)
async def create_opportunity(payload: OpportunityCreate, user: dict = Depends(current_user)):
    customer = await db.customers.find_one({"id": payload.customer_id})
    if not customer:
        raise HTTPException(status_code=400, detail="Customer tidak valid")
    count = await db.opportunities.count_documents({}) + 1
    doc = {"id": new_id(), "opportunity_id": f"OPP-{now().year}-{count:05d}", "customer_name": customer["name"], "sales_id": user["id"], "sales_name": user["name"], **payload.model_dump(mode="json"), "created_at": now()}
    await db.opportunities.insert_one(doc)
    await audit(user, "Create", "Sales Pipeline", doc["id"], {"name": doc["name"]})
    return Opportunity(**doc)


@router.patch("/{opportunity_id}/stage", response_model=Opportunity)
async def update_stage(opportunity_id: str, stage: str, loss_reason: str | None = None, user: dict = Depends(current_user)):
    if stage not in STAGES:
        raise HTTPException(status_code=422, detail="Stage tidak valid")
    if stage == "Lost" and not loss_reason:
        raise HTTPException(status_code=422, detail="Loss reason wajib diisi")
    doc = await db.opportunities.find_one({"id": opportunity_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Opportunity tidak ditemukan")
    update = {"stage": stage, "loss_reason": loss_reason}
    await db.opportunities.update_one({"id": opportunity_id}, {"$set": update})
    await audit(user, "Status Change", "Sales Pipeline", opportunity_id, update)
    return Opportunity(**{**doc, **update})