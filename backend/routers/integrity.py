from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from lib.db import db
from routers.auth import get_current_user
from security.permissions import require_permission

router = APIRouter(prefix="/integrity", tags=["integrity"])


SAMPLE_LIMIT = 20


def _sample(values: list[Any], limit: int = SAMPLE_LIMIT) -> list[Any]:
    return values[:limit]


def _nonempty_exists(field: str) -> dict[str, Any]:
    return {field: {"$exists": True, "$nin": [None, ""]}}


async def _missing_reference(
    collection: str,
    field: str,
    target_collection: str,
    target_field: str = "id",
) -> dict[str, Any]:
    values = await db[collection].distinct(field, _nonempty_exists(field))
    if not values:
        return {"count": 0, "samples": []}

    existing = set(
        await db[target_collection].distinct(
            target_field,
            {target_field: {"$in": values}},
        )
    )
    missing = [value for value in values if value not in existing]
    return {"count": len(missing), "samples": _sample(missing)}


async def _invalid_role_reference(
    collection: str,
    field: str,
    required_roles: set[str],
) -> dict[str, Any]:
    values = await db[collection].distinct(field, _nonempty_exists(field))
    if not values:
        return {"count": 0, "samples": []}

    users = await db.users.find(
        {"id": {"$in": values}},
        {"id": 1, "role": 1},
    ).to_list(None)
    valid = {
        row.get("id")
        for row in users
        if str(row.get("role") or "").strip().upper() in required_roles
    }
    invalid = [value for value in values if value not in valid]
    return {"count": len(invalid), "samples": _sample(invalid)}


async def _duplicate_field(collection: str, field: str) -> dict[str, Any]:
    rows = await db[collection].aggregate([
        {"$match": _nonempty_exists(field)},
        {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": SAMPLE_LIMIT},
    ]).to_list(SAMPLE_LIMIT)
    return {
        "count": sum(item["count"] - 1 for item in rows),
        "samples": [
            {"value": item["_id"], "records": item["count"]}
            for item in rows
        ],
    }


async def _duplicate_ids(collection: str) -> dict[str, Any]:
    return await _duplicate_field(collection, "id")


async def _relationship_mismatch(
    collection: str,
    left_field: str,
    right_collection: str,
    right_field: str,
    link_field: str,
) -> dict[str, Any]:
    query = {
        "$and": [
            _nonempty_exists(left_field),
            _nonempty_exists(link_field),
        ]
    }
    rows = await db[collection].find(
        query,
        {"id": 1, left_field: 1, link_field: 1},
    ).to_list(None)
    if not rows:
        return {"count": 0, "samples": []}

    link_values = list({row.get(link_field) for row in rows if row.get(link_field)})
    linked = await db[right_collection].find(
        {"id": {"$in": link_values}},
        {"id": 1, right_field: 1},
    ).to_list(None)
    by_id = {row.get("id"): row.get(right_field) for row in linked}

    bad = [
        row.get("id")
        for row in rows
        if row.get(link_field) in by_id
        and row.get(left_field) != by_id[row.get(link_field)]
    ]
    return {"count": len(bad), "samples": _sample(bad)}


async def _quotation_number_reference() -> dict[str, Any]:
    values = await db.purchase_orders.distinct(
        "quotation_number",
        _nonempty_exists("quotation_number"),
    )
    if not values:
        return {"count": 0, "samples": []}

    existing = set(
        await db.quotations.distinct(
            "number",
            {"number": {"$in": values}},
        )
    )
    missing = [value for value in values if value not in existing]
    return {"count": len(missing), "samples": _sample(missing)}


@router.get("", response_model=dict)
async def database_integrity_audit(user: dict = Depends(get_current_user)):
    require_permission(user, "integrity.audit")

    collections = [
        "users",
        "customers",
        "products",
        "opportunities",
        "activities",
        "quotations",
        "purchase_orders",
        "sales_targets",
        "tasks",
    ]

    duplicate_ids = {
        name: await _duplicate_ids(name)
        for name in collections
    }

    business_key_duplicates = {
        "users.email": await _duplicate_field("users", "email"),
        "users.user_id": await _duplicate_field("users", "user_id"),
        "customers.customer_id": await _duplicate_field("customers", "customer_id"),
        "products.code": await _duplicate_field("products", "code"),
        "quotations.number": await _duplicate_field("quotations", "number"),
        "purchase_orders.po_number": await _duplicate_field("purchase_orders", "po_number"),
    }

    checks: dict[str, Any] = {
        "users.manager_id -> users.id": await _missing_reference(
            "users", "manager_id", "users"
        ),
        "users.manager_id -> SALES_MANAGER": await _invalid_role_reference(
            "users", "manager_id", {"SALES_MANAGER"}
        ),
        "customers.sales_id -> users.id": await _missing_reference(
            "customers", "sales_id", "users"
        ),
        "customers.sales_id -> SALES": await _invalid_role_reference(
            "customers", "sales_id", {"SALES"}
        ),
        "opportunities.customer_id -> customers.id": await _missing_reference(
            "opportunities", "customer_id", "customers"
        ),
        "opportunities.sales_id -> users.id": await _missing_reference(
            "opportunities", "sales_id", "users"
        ),
        "opportunities.sales_id -> SALES": await _invalid_role_reference(
            "opportunities", "sales_id", {"SALES"}
        ),
        "activities.customer_id -> customers.id": await _missing_reference(
            "activities", "customer_id", "customers"
        ),
        "activities.opportunity_id -> opportunities.id": await _missing_reference(
            "activities", "opportunity_id", "opportunities"
        ),
        "activities.sales_id -> users.id": await _missing_reference(
            "activities", "sales_id", "users"
        ),
        "activities.sales_id -> SALES": await _invalid_role_reference(
            "activities", "sales_id", {"SALES"}
        ),
        "quotations.customer_id -> customers.id": await _missing_reference(
            "quotations", "customer_id", "customers"
        ),
        "quotations.sales_id -> users.id": await _missing_reference(
            "quotations", "sales_id", "users"
        ),
        "quotations.sales_id -> SALES": await _invalid_role_reference(
            "quotations", "sales_id", {"SALES"}
        ),
        "quotations.opportunity_id -> opportunities.id": await _missing_reference(
            "quotations", "opportunity_id", "opportunities"
        ),
        "purchase_orders.customer_id -> customers.id": await _missing_reference(
            "purchase_orders", "customer_id", "customers"
        ),
        "purchase_orders.sales_id -> users.id": await _missing_reference(
            "purchase_orders", "sales_id", "users"
        ),
        "purchase_orders.sales_id -> SALES": await _invalid_role_reference(
            "purchase_orders", "sales_id", {"SALES"}
        ),
        "purchase_orders.quotation_number -> quotations.number": await _quotation_number_reference(),
        "sales_targets.sales_id -> users.id": await _missing_reference(
            "sales_targets", "sales_id", "users"
        ),
        "sales_targets.sales_id -> SALES": await _invalid_role_reference(
            "sales_targets", "sales_id", {"SALES"}
        ),
    }

    checks["activities.customer_id matches opportunity.customer_id"] = await _relationship_mismatch(
        "activities",
        "customer_id",
        "opportunities",
        "customer_id",
        "opportunity_id",
    )
    checks["quotations.customer_id matches opportunity.customer_id"] = await _relationship_mismatch(
        "quotations",
        "customer_id",
        "opportunities",
        "customer_id",
        "opportunity_id",
    )

    product_checks = {
        "quotations.items.product_id -> products.id": await _missing_reference(
            "quotations", "items.product_id", "products"
        ),
        "purchase_orders.items.product_id -> products.id": await _missing_reference(
            "purchase_orders", "items.product_id", "products"
        ),
    }

    task_legacy = await db.tasks.count_documents({
        "$or": [
            {
                "customer_id": {"$exists": False},
                "customer_name": {"$exists": True, "$nin": [None, ""]},
            },
            {
                "opportunity_id": {"$exists": False},
                "opportunity_name": {"$exists": True, "$nin": [None, ""]},
            },
        ]
    })
    checks["tasks legacy name-based records"] = {
        "count": task_legacy,
        "samples": [],
    }

    issue_count = (
        sum(item["count"] for item in checks.values())
        + sum(item["count"] for item in product_checks.values())
        + sum(item["count"] for item in duplicate_ids.values())
        + sum(item["count"] for item in business_key_duplicates.values())
    )

    return {
        "status": "clean" if issue_count == 0 else "issues_found",
        "checked_at": datetime.now(timezone.utc),
        "issue_count": issue_count,
        "checks": checks,
        "product_checks": product_checks,
        "duplicate_ids": duplicate_ids,
        "business_key_duplicates": business_key_duplicates,
        "task_legacy_count": task_legacy,
        "read_only": True,
    }
