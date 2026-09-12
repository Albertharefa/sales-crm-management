import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from routers.deps import current_user
from services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
service = DashboardService()
logger = logging.getLogger(__name__)


@router.get("")
async def dashboard(period: str | None = Query(None), sales_id: str | None = Query(None), stage: str | None = Query(None), customer_id: str | None = Query(None), user: dict = Depends(current_user)):
    try:
        metrics = await service.get_metrics(user, period=period, sales_id=sales_id, stage=stage, customer_id=customer_id)
        if metrics is None:
            raise RuntimeError("DashboardService returned no metrics")

        # DashboardService returns a plain dictionary so MongoDB/BSON values are
        # normalized only at this final HTTP response boundary.
        payload_json = json.loads(json.dumps(metrics, default=str))
        return JSONResponse(content=payload_json)
    except Exception as exc:
        logger.exception("Dashboard aggregation failed for user %s", user.get("id"))
        raise HTTPException(status_code=500, detail="Dashboard gagal dihitung dari database") from exc