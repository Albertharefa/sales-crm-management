import logging

from fastapi import APIRouter, Depends, HTTPException

from models.crm import DashboardMetrics
from routers.deps import current_user
from services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
service = DashboardService()
logger = logging.getLogger(__name__)


@router.get("", response_model=DashboardMetrics)
async def dashboard(user: dict = Depends(current_user)):
    try:
        return await service.get_metrics(user)
    except Exception as exc:
        logger.exception("Dashboard aggregation failed for user %s", user.get("id"))
        raise HTTPException(status_code=500, detail="Dashboard gagal dihitung dari database") from exc