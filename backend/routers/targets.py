from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from lib.db import db
from routers.common import audit, new_id, now
from routers.deps import require_roles

router = APIRouter(tags=["sales-targets"])


class SalesTargetPayload(BaseModel):
    sales_id: str
    year: int = Field(default=2026, ge=2000, le=2100)
    target: float = Field(default=0, ge=0)


@router.get("/sales-targets")
async def list_sales_targets(
    user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER")),
):
    docs = await db.sales_targets.find({}, {"_id": 0}).sort([("year", -1), ("sales_name", 1)]).to_list(5000)
    return docs


@router.post("/sales-targets")
async def create_sales_target(
    payload: SalesTargetPayload,
    user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER")),
):
    sales = await db.users.find_one(
        {"id": payload.sales_id, "role": {"$in": ["SALES", "SALES_MANAGER"]}},
        {"_id": 0, "id": 1, "name": 1},
    )
    if not sales:
        raise HTTPException(status_code=404, detail="Sales tidak ditemukan")

    existing = await db.sales_targets.find_one(
        {"sales_id": payload.sales_id, "year": payload.year}
    )
    if existing:
        await db.sales_targets.update_one(
            {"id": existing["id"]},
            {"$set": {"target": payload.target, "sales_name": sales["name"], "updated_at": now()}},
        )
        doc = await db.sales_targets.find_one({"id": existing["id"]}, {"_id": 0})
        await audit(user, "Update", "Sales Targets", existing["id"], {"sales_id": payload.sales_id, "year": payload.year})
        return doc

    doc = {
        "id": new_id(),
        "sales_id": sales["id"],
        "sales_name": sales["name"],
        "year": payload.year,
        "target": payload.target,
        "created_at": now(),
        "updated_at": now(),
    }
    await db.sales_targets.insert_one(doc)
    doc.pop("_id", None)
    await audit(user, "Create", "Sales Targets", doc["id"], {"sales_id": payload.sales_id, "year": payload.year})
    return doc


@router.put("/sales-targets/{target_id}")
async def update_sales_target(
    target_id: str,
    payload: SalesTargetPayload,
    user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER")),
):
    sales = await db.users.find_one(
        {"id": payload.sales_id, "role": {"$in": ["SALES", "SALES_MANAGER"]}},
        {"_id": 0, "id": 1, "name": 1},
    )
    if not sales:
        raise HTTPException(status_code=404, detail="Sales tidak ditemukan")

    existing = await db.sales_targets.find_one({"id": target_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Target tidak ditemukan")

    duplicate = await db.sales_targets.find_one(
        {"sales_id": payload.sales_id, "year": payload.year, "id": {"$ne": target_id}}
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Target untuk sales dan tahun tersebut sudah ada")

    await db.sales_targets.update_one(
        {"id": target_id},
        {"$set": {
            "sales_id": sales["id"],
            "sales_name": sales["name"],
            "year": payload.year,
            "target": payload.target,
            "updated_at": now(),
        }},
    )
    doc = await db.sales_targets.find_one({"id": target_id}, {"_id": 0})
    await audit(user, "Update", "Sales Targets", target_id, {"sales_id": payload.sales_id, "year": payload.year})
    return doc


@router.delete("/sales-targets/{target_id}")
async def delete_sales_target(
    target_id: str,
    user: dict = Depends(require_roles("SUPER_ADMIN")),
):
    result = await db.sales_targets.delete_one({"id": target_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Target tidak ditemukan")
    await audit(user, "Delete", "Sales Targets", target_id)
    return {"message": "Target berhasil dihapus"}
