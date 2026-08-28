from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from lib.db import db
from models.crm import DashboardMetrics
from routers.deps import current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardMetrics)
async def dashboard(user: dict = Depends(current_user)):
    opportunities = await db.opportunities.find({}).to_list(5000)
    orders = await db.purchase_orders.find({}).to_list(5000)
    pipeline = [o for o in opportunities if o.get("stage") not in ["Won", "Lost"]]
    won = [o for o in opportunities if o.get("stage") == "Won"]
    by_stage = []
    stages = ["Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"]
    for stage in stages:
        items = [o for o in opportunities if o.get("stage") == stage]
        by_stage.append({"stage": stage, "count": len(items), "value": sum(o.get("value", 0) for o in items)})
    today = datetime.now(timezone.utc).date().isoformat()
    completed = len([o for o in orders if o.get("status") == "Completed"])
    return DashboardMetrics(total_customer=await db.customers.count_documents({}), open_pipeline=sum(o.get("value", 0) for o in pipeline), weighted_pipeline=sum(o.get("value", 0) * o.get("probability", 0) / 100 for o in pipeline), won_value=sum(o.get("value", 0) for o in won), total_quotation=await db.quotations.count_documents({}), total_po=len(orders), po_value=sum(o.get("total", 0) for o in orders), activities=await db.activities.count_documents({}), open_orders=len(orders) - completed, completed_orders=completed, overdue_orders=len([o for o in orders if o.get("eta") and o.get("eta") < today and o.get("status") != "Completed"]), pipeline_by_stage=by_stage)