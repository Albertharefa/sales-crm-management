import logging
import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

logger = logging.getLogger("crm.db")
mongodb_url = os.getenv("MONGODB_URI") or os.getenv("MONGO_URL") or "mongodb://localhost:27017"
db_name = os.getenv("DB_NAME", "sales_crm_db")

client = AsyncIOMotorClient(
    mongodb_url,
    maxPoolSize=50,
    minPoolSize=5,
    serverSelectionTimeoutMS=5000,
)
db = client[db_name]
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def connect_to_mongo():
    try:
        await client.admin.command("ping")
        await _ensure_indexes()
        await db.sessions.delete_many({"expires_at": {"$lte": datetime.now(timezone.utc)}})
        logger.info("MongoDB connection OK: %s", db_name)
    except Exception as exc:
        logger.error("MongoDB connection failed: %s", exc)
        raise


async def _repair_sales_target_integrity():
    """Repair legacy target rows before enforcing the one-user/one-year rule.

    The repair is intentionally idempotent. It uses users.id as the canonical
    owner identity/name, removes only duplicate rows for the same sales_id/year,
    and keeps the most recently updated row for each duplicate group.
    """
    users = await db.users.find(
        {"role": {"$in": ["SALES_MANAGER", "SALES"]}},
        {"_id": 0, "id": 1, "name": 1, "role": 1},
    ).to_list(5000)
    owners = {str(item["id"]): item for item in users if item.get("id")}

    docs = await db.sales_targets.find({}, {"_id": 0}).to_list(10000)
    groups: dict[tuple[str, int], list[dict]] = {}

    for doc in docs:
        sales_id = str(doc.get("sales_id") or "").strip()
        if not sales_id or sales_id not in owners:
            continue
        try:
            year = int(doc.get("year"))
        except (TypeError, ValueError):
            continue

        owner = owners[sales_id]
        changes = {}
        canonical_name = str(owner.get("name") or "").strip()
        canonical_role = str(owner.get("role") or "SALES").strip().upper()
        if canonical_name and doc.get("sales_name") != canonical_name:
            changes["sales_name"] = canonical_name
        if doc.get("owner_role") != canonical_role:
            changes["owner_role"] = canonical_role
        if doc.get("year") != year:
            changes["year"] = year
        if changes:
            await db.sales_targets.update_one({"id": doc.get("id")}, {"$set": changes})
            doc.update(changes)

        groups.setdefault((sales_id, year), []).append(doc)

    duplicate_groups = 0
    removed = 0
    for key, rows in groups.items():
        if len(rows) <= 1:
            continue
        duplicate_groups += 1
        rows.sort(
            key=lambda row: (
                row.get("updated_at") or datetime.min.replace(tzinfo=timezone.utc),
                row.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                str(row.get("id") or ""),
            ),
            reverse=True,
        )
        keep = rows[0]
        delete_ids = [str(row.get("id")) for row in rows[1:] if row.get("id")]
        if delete_ids:
            result = await db.sales_targets.delete_many({"id": {"$in": delete_ids}})
            removed += int(result.deleted_count or 0)
        logger.warning(
            "Sales target duplicate cleanup: owner=%s year=%s kept=%s removed=%s",
            key[0], key[1], keep.get("id"), len(delete_ids),
        )

    if duplicate_groups or removed:
        logger.info(
            "Sales target integrity repair complete: duplicate_groups=%s removed=%s",
            duplicate_groups, removed,
        )


async def _ensure_indexes():
    """Create production indexes and enforce sales-target data integrity."""
    # Repair legacy duplicate/stale-name rows before creating the unique index.
    await _repair_sales_target_integrity()

    indexes = {
        "users": [
            ([('id', 1)], "users_id"),
            ([('email', 1)], "users_email"),
            ([('user_id', 1)], "users_user_id"),
            ([('role', 1), ('status', 1)], "users_role_status"),
            ([('manager_id', 1), ('role', 1)], "users_manager_role"),
        ],
        "sessions": [
            ([('token', 1)], "sessions_token"),
            ([('user_id', 1), ('expires_at', 1)], "sessions_user_expiry"),
            ([('expires_at', 1)], "sessions_expiry"),
        ],
        "password_reset_tokens": [
            ([('token_hash', 1)], "password_reset_token"),
            ([('user_id', 1), ('expires_at', 1)], "password_reset_user_expiry"),
        ],
        "audit_logs": [
            ([('created_at', -1)], "audit_created_at"),
            ([('user_id', 1), ('created_at', -1)], "audit_user_created"),
        ],
        "customers": [
            ([('id', 1)], "customers_id"),
            ([('customer_id', 1)], "customers_customer_id"),
            ([('sales_id', 1), ('status', 1)], "customers_sales_status"),
            ([('name', 1)], "customers_name"),
            ([('is_demo', 1)], "customers_demo"),
        ],
        "contacts": [
            ([('customer_id', 1), ('created_at', -1)], "contacts_customer_created"),
        ],
        "products": [
            ([('id', 1)], "products_id"),
            ([('code', 1)], "products_code"),
            ([('brand', 1), ('category', 1)], "products_brand_category"),
            ([('status', 1)], "products_status"),
            ([('is_demo', 1)], "products_demo"),
        ],
        "opportunities": [
            ([('id', 1)], "opportunities_id"),
            ([('customer_id', 1)], "opportunities_customer"),
            ([('sales_id', 1)], "opportunities_sales"),
            ([('stage', 1), ('status', 1)], "opportunities_stage_status"),
            ([('is_demo', 1)], "opportunities_demo"),
        ],
        "activities": [
            ([('id', 1)], "activities_id"),
            ([('customer_id', 1), ('created_at', -1)], "activities_customer_created"),
            ([('opportunity_id', 1)], "activities_opportunity"),
            ([('sales_id', 1), ('created_at', -1)], "activities_sales_created"),
            ([('status', 1), ('type', 1)], "activities_status_type"),
            ([('is_demo', 1)], "activities_demo"),
        ],
        "quotations": [
            ([('id', 1)], "quotations_id"),
            ([('number', 1)], "quotations_number_field"),
            ([('customer_id', 1)], "quotations_customer"),
            ([('sales_id', 1)], "quotations_sales"),
            ([('opportunity_id', 1)], "quotations_opportunity"),
            ([('status', 1), ('created_at', -1)], "quotations_status_created"),
            ([('is_demo', 1)], "quotations_demo"),
        ],
        "purchase_orders": [
            ([('id', 1)], "purchase_orders_id"),
            ([('po_number', 1)], "purchase_orders_number"),
            ([('customer_id', 1)], "purchase_orders_customer"),
            ([('sales_id', 1)], "purchase_orders_sales"),
            ([('quotation_number', 1)], "purchase_orders_quotation"),
            ([('status', 1), ('eta', 1)], "purchase_orders_status_eta"),
            ([('is_demo', 1)], "purchase_orders_demo"),
        ],
        "sales_targets": [
            ([('id', 1)], "sales_targets_id", False),
            ([('sales_id', 1), ('year', 1)], "sales_targets_sales_year", True),
            ([('year', 1), ('status', 1)], "sales_targets_year_status", False),
            ([('is_demo', 1)], "sales_targets_demo", False),
        ],
        "tasks": [
            ([('id', 1)], "tasks_id"),
            ([('assigned_user', 1), ('status', 1)], "tasks_assignee_status"),
            ([('customer_name', 1)], "tasks_customer"),
            ([('opportunity_name', 1)], "tasks_opportunity"),
            ([('is_demo', 1)], "tasks_demo"),
        ],
    }

    for collection_name, collection_indexes in indexes.items():
        collection = db[collection_name]
        for index_spec in collection_indexes:
            keys, name = index_spec[0], index_spec[1]
            unique = bool(index_spec[2]) if len(index_spec) > 2 else False
            try:
                if collection_name == "sales_targets" and name == "sales_targets_sales_year":
                    try:
                        await collection.drop_index(name)
                    except Exception:
                        pass
                await collection.create_index(keys, name=name, unique=unique)
            except Exception as exc:
                logger.warning("Index %s.%s could not be created: %s", collection_name, name, exc)


async def ensure_admin_user():
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not email or not password:
        logger.warning("ADMIN_EMAIL/ADMIN_PASSWORD not configured; admin auto-seed skipped")
        return

    existing = await db.users.find_one({"email": email})
    # Never perform password hashing/reset during application startup.
    if existing:
        return

    import uuid
    user = {
        "id": str(uuid.uuid4()),
        "user_id": "USR-ADMIN",
        "name": "Super Admin",
        "email": email,
        "role": "SUPER_ADMIN",
        "status": "Active",
        "password_hash": pwd_context.hash(password),
        "failed_login_attempts": 0,
        "locked_until": None,
        "created_at": datetime.now(timezone.utc),
    }
    await db.users.insert_one(user)
    logger.info("CRM admin user auto-created: %s", email)


async def close_mongo_connection():
    client.close()
    logger.info("MongoDB connection closed")