"""One-time legacy data cleanup kept under the historical seed module name.

The production CRM must use the live MongoDB records created through the CRM
workflows. The previous demo seed inserted fixed demo users, customers,
pipeline records, quotations, purchase orders, activities, and products on
every application startup. That behavior is intentionally disabled.

This function is still called by the existing application lifespan so an
existing production database is cleaned automatically during deployment.
Only records that are explicitly marked as demo or match the known legacy
seed signatures are removed; normal live CRM records are preserved.
"""
import re

from lib.db import db


LEGACY_CUSTOMER_RE = re.compile(r"^CUS-2026-\d{5}$")
LEGACY_OPPORTUNITY_RE = re.compile(r"^OPP-2026-\d{5}$")
LEGACY_QUOTATION_RE = re.compile(r"^QT-2026-\d{5}$")
LEGACY_PRODUCT_RE = re.compile(r"^PRD-\d{4}$")
LEGACY_PO_RE = re.compile(r"^PO/CUST/2026/\d{4}$")
LEGACY_ACTIVITY_RE = re.compile(r"^ACT-\d{5}$")


async def _delete_demo_marked_records() -> dict[str, int]:
    collections = [
        "users",
        "customers",
        "contacts",
        "leads",
        "opportunities",
        "quotations",
        "purchase_orders",
        "activities",
        "tasks",
        "projects",
        "tenders",
        "audit_logs",
        "documents",
        "sales_targets",
    ]
    deleted: dict[str, int] = {}
    for collection in collections:
        result = await db[collection].delete_many({"is_demo": True})
        if result.deleted_count:
            deleted[collection] = int(result.deleted_count)
    return deleted


async def _delete_legacy_seed_records() -> dict[str, int]:
    deleted: dict[str, int] = {}

    legacy_user_ids = ["admin-0001", "manager-0001", "sales-0001"]
    result = await db.users.delete_many({"id": {"$in": legacy_user_ids}})
    if result.deleted_count:
        deleted["users_legacy"] = int(result.deleted_count)

    result = await db.products.delete_many({
        "code": {"$regex": LEGACY_PRODUCT_RE.pattern},
        "description": "Industrial automation and engineering product",
    })
    if result.deleted_count:
        deleted["products_legacy"] = int(result.deleted_count)

    result = await db.customers.delete_many({
        "customer_id": {"$regex": LEGACY_CUSTOMER_RE.pattern},
        "sales_id": "sales-0001",
    })
    if result.deleted_count:
        deleted["customers_legacy"] = int(result.deleted_count)

    result = await db.opportunities.delete_many({
        "opportunity_id": {"$regex": LEGACY_OPPORTUNITY_RE.pattern},
        "sales_id": "sales-0001",
        "sales_name": "Budi Santoso",
    })
    if result.deleted_count:
        deleted["opportunities_legacy"] = int(result.deleted_count)

    result = await db.quotations.delete_many({
        "number": {"$regex": LEGACY_QUOTATION_RE.pattern},
        "customer_name": {"$regex": r"^PT Industri \d{2}$"},
        "sales_name": "Budi Santoso",
    })
    if result.deleted_count:
        deleted["quotations_legacy"] = int(result.deleted_count)

    result = await db.purchase_orders.delete_many({
        "po_number": {"$regex": LEGACY_PO_RE.pattern},
        "customer_name": {"$regex": r"^PT Industri \d{2}$"},
        "sales_name": "Budi Santoso",
    })
    if result.deleted_count:
        deleted["purchase_orders_legacy"] = int(result.deleted_count)

    result = await db.activities.delete_many({
        "activity_id": {"$regex": LEGACY_ACTIVITY_RE.pattern},
        "customer_name": {"$regex": r"^PT Industri \d{2}$"},
        "sales_name": "Budi Santoso",
    })
    if result.deleted_count:
        deleted["activities_legacy"] = int(result.deleted_count)

    result = await db.tasks.delete_many({"assigned_user": "Budi Santoso"})
    if result.deleted_count:
        deleted["tasks_legacy"] = int(result.deleted_count)

    return deleted


async def _reset_empty_legacy_sequences() -> None:
    """Remove old counters only when no live quotations/orders remain."""
    if await db.quotations.count_documents({}) == 0:
        await db.number_sequences.delete_many({"key": {"$regex": r"^QT-2026$"}})


async def seed_demo_data():
    """Clean the old demo/seed database; never insert demo records."""
    deleted_demo = await _delete_demo_marked_records()
    deleted_legacy = await _delete_legacy_seed_records()
    await _reset_empty_legacy_sequences()

    total_deleted = sum(deleted_demo.values()) + sum(deleted_legacy.values())
    if total_deleted:
        print(f"Legacy CRM demo cleanup complete: {total_deleted} records removed")
    else:
        print("Legacy CRM demo cleanup complete: no legacy demo records found")
