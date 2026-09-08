import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from routers.deps import current_user
from services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
service = DashboardService()
logger = logging.getLogger(__name__)


@router.get("")
async def dashboard(user: dict = Depends(current_user)):
    try:
        metrics = await service.get_metrics(user)
        if metrics is None:
            raise RuntimeError("DashboardService returned no metrics")

        # Keep BSON/Pydantic serialization out of FastAPI's response_model path.
        # model_dump() keeps Python values intact, then json.dumps(default=str)
        # converts any BSON ObjectId/date-like values safely at the final boundary.
        payload = metrics.model_dump()
        payload_json = json.loads(json.dumps(payload, default=str))
        return JSONResponse(content=payload_json)
    except Exception as exc:
        logger.exception("Dashboard aggregation failed for user %s", user.get("id"))
        raise HTTPException(
            status_code=500,
            detail="Dashboard gagal dihitung dari database",
        ) from exc
