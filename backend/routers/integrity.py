from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from lib.db import db
from routers.auth import get_current_user
from security.permissions import require_permission

router = APIRouter(prefix="/integrity", tags=["integrity"])


def _sample(values: list[Any], limit: int = 20) -> list[Any]:
    return values[:limit]


async def _missing_reference(collection: str, field: str, target_collection: str, target_field: str = "id") -> dict[str, Any]:
    values = await db[collection].distinct(field, {field: {"$exists": True, "$ne": None, "$ne": ""}})
    if not values:
        return {"count": 0, "samples": []}
    existing = set(await db[target_collection].distinct(target_field, {target_field: {"$in": values}}))
    missing = [value for value in values if value not in existing]
    return {"count": len(missing), "samples": _sample(missing)}


async def _duplicate_ids(collection: str) -> dict[str, Any]:
    rows = await db[collection].aggregate([
        {"$match": {"id": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20},
    ]).to_list(20)
    return {"count": sum(item["count"] - 1 for item in rows), "samples": [{"id": item["_id"], "records": item["count"]} for item in rows]}


async def _relationship_mismatch(collection: str, left_field: str, right_collection: str, right_field: str, link_field: str) -> dict[str, Any]:
    rows = await db[collection].find({left_field: {"$exists": True, "$ne": None, "$ne": ""}, link_field: {"$exists": True, "$ne": None, "$ne": ""}}, {"id": 1, left_field: 1, link_field: 1}).to_list(None)
    if not rows:
        return {"count": 0, "samples": []}
    link_values = list({row.get(link_field) for row in rows if row.get(link_field)})
    linked = await db[right_collection].find({"id": {"$in": link_values}}, {"id": 1, right_field: 1}).to_list(None)
    by_id = {row.get("id"): row.get(right_field) for row in linked}
    bad = [row.get("id") for row in rows if row.get(link_field) in by_id and row.get(left_field) != by_id[row.get(link_field)]]
    return {"count": len(bad), "samples": _sample(bad)}


@router.get("", response_model=dict)
async def database_integrity_audit(user: dict = Depends(get_current_user)):
    require_permission(user, "integrity.audit")

    collections = ["users", "customers", "products", "opportunities", "activities", "quotations", "purchase_orders", "sales_targets", "tasks"]
    duplicates = {name: await _duplicate_ids(name) for name in collections}

    checks: dict[str, Any] = {
        "users.manager_id -> users.id": await _missing_reference("users", "manager_id", "users"),
        "customers.sales_id -> users.id": await _missing_reference("customers", "sales_id", "users"),
        "opportunities.customer_id -> customers.id": await _missing_reference("opportunities", "customer_id", "customers"),
        "opportunities.sales_id -> users.id": await _missing_reference("opportunities", "sales_id", "users"),
        "activities.customer_id -> customers.id": await _missing_reference("activities", "customer_id", "customers"),
        "activities.opportunity_id -> opportunities.id": await _missing_reference("activities", "opportunity_id", "opportunities"),
        "activities.sales_id -> users.id": await _missing_reference("activities", "sales_id", "users"),
        "quotations.customer_id -> customers.id": await _missing_reference("quotations", "customer_id", "customers"),
        "quotations.sales_id -> users.id": await _missing_reference("quotations", "sales_id", "users"),
        "quotations.opportunity_id -> opportunities.id": await _missing_reference("quotations", "opportunity_id", "opportunities"),
        "purchase_orders.customer_id -> customers.id": await _missing_reference("purchase_orders", "customer_id", "customers"),
        "purchase_orders.sales_id -> users.id": await _missing_reference("purchase_orders", "sales_id", "users"),
        "sales_targets.sales_id -> users.id": await _missing_reference("sales_targets", "sales_id", "users"),
    }

    checks["activities.customer_id matches opportunity.customer_id"] = await _relationship_mismatch("activities", "customer_id", "opportunities", "customer_id", "opportunity_id")
    checks["quotations.customer_id matches opportunity.customer_id"] = await _relationship_mismatch("quotations", "customer_id", "opportunities", "customer_id", "opportunity_id")

    task_legacy = await db.tasks.count_documents({"$or": [
        {"customer_id": {"$exists": False}, "customer_name": {"$exists": True}},
        {"opportunity_id": {"$exists": False}, "opportunity_name": {"$exists": True}},
    ]})
    checks["tasks legacy name-based records"] = {"count": task_legacy, "samples": []}

    product_checks = {}
    product_checks["quotations.items.product_id -> products.id"] = await _missing_reference("quotations", "items.product_id", "products")
    product_checks["purchase_orders.items.product_id -> products.id"] = await _missing_reference("purchase_orders", "items.product_id", "products")

    issue_count = sum(item["count"] for item in checks.values()) + sum(item["count"] for item in product_checks.values()) + sum(item["count"] for item in duplicates.values())
    issue_count += task_legacy

    return {
        "status": "clean" if issue_count == 0 else "issues_found",
        "checked_at": datetime.now(timezone.utc),
        "issue_count": issue_count,
        "checks": checks,
        "product_checks": product_checks,
        "duplicate_ids": duplicates,
        "task_legacy_count": task_legacy,
        "read_only": True,
    }
