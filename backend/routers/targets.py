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


async def visible_sales_ids(user: dict) -> list[str] | None:
    """Return sales IDs visible for target management; None means unrestricted."""
    if user.get("role") == "SUPER_ADMIN":
        return None

    reports = await db.users.find(
        {"manager_id": user["id"], "role": "SALES"},
        {"_id": 0, "id": 1},
    ).to_list(1000)
    return [str(item["id"]) for item in reports if item.get("id")]


async def get_sales_for_target(sales_id: str, user: dict) -> dict:
    """Validate the target owner and enforce manager hierarchy."""
    sales = await db.users.find_one(
        {"id": sales_id, "role": "SALES"},
        {"_id": 0, "id": 1, "name": 1, "role": 1, "status": 1, "manager_id": 1},
    )
    if not sales:
        raise HTTPException(status_code=404, detail="Sales tidak ditemukan")

    if user.get("role") == "SALES_MANAGER" and sales.get("manager_id") != user.get("id"):
        raise HTTPException(status_code=403, detail="Sales tersebut bukan anggota team Anda")

    return sales


@router.get("/sales-targets")
async def list_sales_targets(
    user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER")),
):
    allowed_ids = await visible_sales_ids(user)
    query = {} if allowed_ids is None else {"sales_id": {"$in": allowed_ids}}

    docs = await db.sales_targets.find(
        query,
        {"_id": 0},
    ).sort([("year", -1), ("sales_name", 1)]).to_list(5000)

    sales_ids = [str(item.get("sales_id") or "").strip() for item in docs if item.get("sales_id")]
    users = await db.users.find(
        {"id": {"$in": sales_ids}, "role": "SALES"},
        {"_id": 0, "id": 1, "status": 1},
    ).to_list(1000) if sales_ids else []
    status_by_id = {
        str(item.get("id")): str(item.get("status") or "Active").strip().upper()
        for item in users
    }
    valid_sales_ids = set(status_by_id)

    # A sales target is valid only when its authoritative sales_id still
    # belongs to a SALES user. Keep inactive SALES users visible so the
    # existing Active/Inactive filter remains meaningful.
    docs = [item for item in docs if str(item.get("sales_id") or "") in valid_sales_ids]

    for item in docs:
        status = status_by_id.get(str(item.get("sales_id") or ""), "ACTIVE")
        item["sales_status"] = "Inactive" if status in {"INACTIVE", "DISABLED"} else "Active"

    return docs


@router.get("/sales-targets/options")
async def sales_target_options(
    user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER")),
):
    """Return only active SALES users the current user may manage."""
    query = {
        "role": "SALES",
        "status": {"$nin": ["INACTIVE", "DISABLED"]},
    }
    if user.get("role") == "SALES_MANAGER":
        query["manager_id"] = user["id"]

    users = await db.users.find(
        query,
        {"_id": 0, "id": 1, "name": 1},
    ).sort("name", 1).to_list(1000)
    return [
        {"id": str(item["id"]), "name": str(item["name"])}
        for item in users
        if item.get("id") and item.get("name")
    ]


@router.post("/sales-targets")
async def create_sales_target(
    payload: SalesTargetPayload,
    user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER")),
):
    sales = await get_sales_for_target(payload.sales_id, user)

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
    sales = await get_sales_for_target(payload.sales_id, user)

    existing = await db.sales_targets.find_one({"id": target_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Target tidak ditemukan")

    if user.get("role") == "SALES_MANAGER" and existing.get("sales_id") not in (await visible_sales_ids(user) or []):
        raise HTTPException(status_code=403, detail="Target tersebut bukan milik team Anda")

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
    user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER")),
):
    existing = await db.sales_targets.find_one({"id": target_id}, {"_id": 0, "sales_id": 1})
    if not existing:
        raise HTTPException(status_code=404, detail="Target tidak ditemukan")

    if user.get("role") == "SALES_MANAGER" and existing.get("sales_id") not in (await visible_sales_ids(user) or []):
        raise HTTPException(status_code=403, detail="Target tersebut bukan milik team Anda")

    result = await db.sales_targets.delete_one({"id": target_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Target tidak ditemukan")
    await audit(user, "Delete", "Sales Targets", target_id)
    return {"message": "Target berhasil dihapus"}
