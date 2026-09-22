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


async def visible_owner_ids(user: dict) -> list[str] | None:
    role = str(user.get("role") or "").strip().upper()
    if role == "SUPER_ADMIN":
        docs = await db.users.find({"role": {"$in": ["SALES_MANAGER", "SALES"]}}, {"_id": 0, "id": 1}).to_list(1000)
        return [str(item["id"]) for item in docs if item.get("id")]
    if role == "SALES_MANAGER":
        reports = await db.users.find({"manager_id": user["id"], "role": "SALES"}, {"_id": 0, "id": 1}).to_list(1000)
        return [str(user["id"]), *[str(item["id"]) for item in reports if item.get("id")]]
    return [str(user.get("id"))] if user.get("id") else []


async def get_target_owner(owner_id: str, user: dict) -> dict:
    owner = await db.users.find_one({"id": owner_id, "role": {"$in": ["SALES_MANAGER", "SALES"]}}, {"_id": 0, "id": 1, "name": 1, "role": 1, "status": 1, "manager_id": 1})
    if not owner:
        raise HTTPException(status_code=404, detail="User target tidak ditemukan")
    role = str(user.get("role") or "").strip().upper()
    if role == "SALES_MANAGER" and owner["id"] != user.get("id") and owner.get("manager_id") != user.get("id"):
        raise HTTPException(status_code=403, detail="User tersebut bukan anggota team Anda")
    if role == "SALES" and owner["id"] != user.get("id"):
        raise HTTPException(status_code=403, detail="Anda hanya dapat melihat target Anda sendiri")
    return owner


async def _achievement_by_owner(owner_rows: list[dict], year: int) -> dict[str, float]:
    """Return PO achievement by sales user for the requested calendar year."""
    if not owner_rows:
        return {}
    ids = [str(row.get("id")) for row in owner_rows if row.get("id")]
    names = [str(row.get("name")) for row in owner_rows if row.get("name")]
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    pipeline = [
        {"$set": {
            "safe_date": {"$convert": {"input": "$date", "to": "date", "onError": None, "onNull": None}},
            "safe_total": {"$convert": {"input": "$total", "to": "double", "onError": 0, "onNull": 0}},
            "safe_sales_id": {"$toString": {"$ifNull": ["$sales_id", ""]}},
            "safe_sales_name": {"$ifNull": ["$sales_name", ""]},
        }},
        {"$match": {"safe_date": {"$gte": start, "$lt": end}, "$or": [{"safe_sales_id": {"$in": ids}}, {"safe_sales_name": {"$in": names}}]}},
        {"$group": {"_id": {"sales_id": "$safe_sales_id", "sales_name": "$safe_sales_name"}, "achievement": {"$sum": "$safe_total"}}},
    ]
    rows = await db.purchase_orders.aggregate(pipeline, allowDiskUse=False).to_list(5000)
    result: dict[str, float] = {}
    by_name = {str(row.get("name")): str(row.get("id")) for row in owner_rows if row.get("id") and row.get("name")}
    for row in rows:
        key = str((row.get("_id") or {}).get("sales_id") or "")
        name = str((row.get("_id") or {}).get("sales_name") or "")
        owner_id = key if key in ids else by_name.get(name)
        if owner_id:
            result[owner_id] = result.get(owner_id, 0.0) + float(row.get("achievement", 0) or 0)
    return result


def _achievement_pct(achievement: float, target: float) -> float:
    return round((achievement / target) * 100, 2) if target > 0 else 0.0


def _member_row(item: dict, target_by_id: dict[str, float], achievement_by_id: dict[str, float], role: str | None = None) -> dict:
    owner_id = str(item["id"])
    target = float(target_by_id.get(owner_id, 0.0))
    achievement = float(achievement_by_id.get(owner_id, 0.0))
    return {"id": owner_id, "name": str(item["name"]), "role": role or str(item.get("role") or "SALES"), "target": target, "achievement": achievement, "achievement_pct": _achievement_pct(achievement, target)}


@router.get("/sales-targets")
async def list_sales_targets(user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER", "SALES"))):
    allowed_ids = await visible_owner_ids(user)
    query = {} if allowed_ids is None else {"sales_id": {"$in": allowed_ids}}
    docs = await db.sales_targets.find(query, {"_id": 0}).sort([("year", -1), ("sales_name", 1)]).to_list(5000)
    owner_ids = [str(item.get("sales_id") or "").strip() for item in docs if item.get("sales_id")]
    users = await db.users.find({"id": {"$in": owner_ids}, "role": {"$in": ["SALES_MANAGER", "SALES"]}}, {"_id": 0, "id": 1, "status": 1, "role": 1, "manager_id": 1}).to_list(1000) if owner_ids else []
    by_id = {str(item["id"]): item for item in users}
    docs = [item for item in docs if str(item.get("sales_id") or "") in by_id]
    for item in docs:
        owner = by_id.get(str(item.get("sales_id"))) or {}
        status = str(owner.get("status") or "Active").strip().upper()
        item["owner_role"] = owner.get("role", "SALES")
        item["sales_status"] = "Inactive" if status in {"INACTIVE", "DISABLED"} else "Active"
    return docs


@router.get("/sales-targets/options")
async def sales_target_options(user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER", "SALES"))):
    role = str(user.get("role") or "").strip().upper()
    query = {"role": {"$in": ["SALES", "SALES_MANAGER"]}, "status": {"$nin": ["INACTIVE", "DISABLED"]}}
    if role == "SALES_MANAGER":
        query = {"$or": [{"id": user["id"]}, {"manager_id": user["id"], "role": "SALES"}], "status": {"$nin": ["INACTIVE", "DISABLED"]}}
    elif role == "SALES":
        query = {"id": user["id"], "role": "SALES", "status": {"$nin": ["INACTIVE", "DISABLED"]}}
    users = await db.users.find(query, {"_id": 0, "id": 1, "name": 1, "role": 1}).sort("name", 1).to_list(1000)
    return [{"id": str(item["id"]), "name": str(item["name"]), "role": str(item.get("role") or "SALES")} for item in users if item.get("id") and item.get("name")]


@router.get("/sales-targets/summary")
async def sales_target_summary(year: int = 2026, user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER", "SALES"))):
    role = str(user.get("role") or "").strip().upper()
    if role == "SALES":
        owner = await db.users.find_one({"id": user["id"], "role": "SALES"}, {"_id": 0, "id": 1, "name": 1, "role": 1})
        if not owner:
            raise HTTPException(status_code=404, detail="User target tidak ditemukan")
        owner_rows = [owner]
        targets = await db.sales_targets.find({"year": year, "sales_id": user["id"]}, {"_id": 0, "sales_id": 1, "sales_name": 1, "target": 1}).to_list(10)
        target_by_id = {str(item.get("sales_id")): float(item.get("target", 0) or 0) for item in targets}
        achievement_by_id = await _achievement_by_owner(owner_rows, year)
        row = _member_row(owner, target_by_id, achievement_by_id, "SALES")
        return {"year": year, "personal_target": row["target"], "personal_achievement": row["achievement"], "personal_achievement_pct": row["achievement_pct"], "team_target": row["target"], "team_achievement": row["achievement"], "team_achievement_pct": row["achievement_pct"], "manager": {"id": owner["id"], "name": owner["name"], "role": owner["role"]}, "members": [row]}

    if role == "SALES_MANAGER":
        manager = await db.users.find_one({"id": user["id"], "role": "SALES_MANAGER"}, {"_id": 0, "id": 1, "name": 1, "role": 1})
        members = await db.users.find({"manager_id": user["id"], "role": "SALES"}, {"_id": 0, "id": 1, "name": 1, "role": 1}).sort("name", 1).to_list(1000)
        owner_rows = [{"id": user["id"], "name": manager["name"], "role": "SALES_MANAGER"}, *members]
        owner_ids = [str(item["id"]) for item in owner_rows]
        targets = await db.sales_targets.find({"year": year, "sales_id": {"$in": owner_ids}}, {"_id": 0, "sales_id": 1, "sales_name": 1, "target": 1}).to_list(5000)
        target_by_id = {str(item.get("sales_id")): float(item.get("target", 0) or 0) for item in targets}
        achievement_by_id = await _achievement_by_owner(owner_rows, year)
        personal = target_by_id.get(str(user["id"]), 0.0)
        personal_achievement = float(achievement_by_id.get(str(user["id"]), 0.0))
        member_rows = [_member_row(item, target_by_id, achievement_by_id, "SALES") for item in members]
        manager_row = _member_row({"id": user["id"], "name": manager["name"]}, target_by_id, achievement_by_id, "SALES_MANAGER")
        team = personal + sum(float(item["target"]) for item in member_rows)
        team_achievement = personal_achievement + sum(float(item["achievement"]) for item in member_rows)
        return {"year": year, "personal_target": personal, "personal_achievement": personal_achievement, "personal_achievement_pct": _achievement_pct(personal_achievement, personal), "team_target": team, "team_achievement": team_achievement, "team_achievement_pct": _achievement_pct(team_achievement, team), "manager": {"id": manager["id"], "name": manager["name"], "role": manager["role"]}, "members": [manager_row, *member_rows]}

    users = await db.users.find({"role": {"$in": ["SALES_MANAGER", "SALES"]}}, {"_id": 0, "id": 1, "name": 1, "role": 1, "manager_id": 1}).sort("name", 1).to_list(2000)
    targets = await db.sales_targets.find({"year": year}, {"_id": 0, "sales_id": 1, "sales_name": 1, "target": 1}).to_list(5000)
    target_by_id = {str(item.get("sales_id")): float(item.get("target", 0) or 0) for item in targets}
    achievement_by_id = await _achievement_by_owner(users, year)
    managers = []
    for manager in [item for item in users if item.get("role") == "SALES_MANAGER"]:
        members = [item for item in users if item.get("manager_id") == manager.get("id") and item.get("role") == "SALES"]
        manager_row = _member_row(manager, target_by_id, achievement_by_id, "SALES_MANAGER")
        member_rows = [_member_row(item, target_by_id, achievement_by_id, "SALES") for item in members]
        personal = manager_row["target"]
        personal_achievement = manager_row["achievement"]
        team = personal + sum(float(item["target"]) for item in member_rows)
        team_achievement = personal_achievement + sum(float(item["achievement"]) for item in member_rows)
        managers.append({"id": str(manager["id"]), "name": str(manager["name"]), "personal_target": personal, "personal_achievement": personal_achievement, "personal_achievement_pct": _achievement_pct(personal_achievement, personal), "team_target": team, "team_achievement": team_achievement, "team_achievement_pct": _achievement_pct(team_achievement, team), "members": [manager_row, *member_rows]})
    return {"year": year, "managers": managers}


@router.post("/sales-targets")
async def create_sales_target(payload: SalesTargetPayload, user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER"))):
    owner = await get_target_owner(payload.sales_id, user)
    existing = await db.sales_targets.find_one({"sales_id": payload.sales_id, "year": payload.year})
    if existing:
        await db.sales_targets.update_one({"id": existing["id"]}, {"$set": {"target": payload.target, "sales_name": owner["name"], "updated_at": now()}})
        doc = await db.sales_targets.find_one({"id": existing["id"]}, {"_id": 0})
        await audit(user, "Update", "Sales Targets", existing["id"], {"sales_id": payload.sales_id, "year": payload.year})
        return doc
    doc = {"id": new_id(), "sales_id": owner["id"], "sales_name": owner["name"], "owner_role": owner["role"], "year": payload.year, "target": payload.target, "created_at": now(), "updated_at": now()}
    await db.sales_targets.insert_one(doc)
    doc.pop("_id", None)
    await audit(user, "Create", "Sales Targets", doc["id"], {"sales_id": payload.sales_id, "year": payload.year, "owner_role": owner["role"]})
    return doc


@router.put("/sales-targets/{target_id}")
async def update_sales_target(target_id: str, payload: SalesTargetPayload, user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER"))):
    owner = await get_target_owner(payload.sales_id, user)
    existing = await db.sales_targets.find_one({"id": target_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Target tidak ditemukan")
    if user.get("role") == "SALES_MANAGER" and existing.get("sales_id") not in (await visible_owner_ids(user) or []):
        raise HTTPException(status_code=403, detail="Target tersebut bukan milik Anda atau team Anda")
    duplicate = await db.sales_targets.find_one({"sales_id": payload.sales_id, "year": payload.year, "id": {"$ne": target_id}})
    if duplicate:
        raise HTTPException(status_code=409, detail="Target untuk user dan tahun tersebut sudah ada")
    await db.sales_targets.update_one({"id": target_id}, {"$set": {"sales_id": owner["id"], "sales_name": owner["name"], "owner_role": owner["role"], "year": payload.year, "target": payload.target, "updated_at": now()}})
    doc = await db.sales_targets.find_one({"id": target_id}, {"_id": 0})
    await audit(user, "Update", "Sales Targets", target_id, {"sales_id": payload.sales_id, "year": payload.year})
    return doc


@router.delete("/sales-targets/{target_id}")
async def delete_sales_target(target_id: str, user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER"))):
    existing = await db.sales_targets.find_one({"id": target_id}, {"_id": 0, "sales_id": 1})
    if not existing:
        raise HTTPException(status_code=404, detail="Target tidak ditemukan")
    if user.get("role") == "SALES_MANAGER" and existing.get("sales_id") not in (await visible_owner_ids(user) or []):
        raise HTTPException(status_code=403, detail="Target tersebut bukan milik Anda atau team Anda")
    result = await db.sales_targets.delete_one({"id": target_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Target tidak ditemukan")
    await audit(user, "Delete", "Sales Targets", target_id)
    return {"message": "Target berhasil dihapus"}
