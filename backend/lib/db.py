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


async def _ensure_indexes():
    """Create safe, non-unique indexes used by the production CRM.

    Index creation is idempotent and runs automatically at application startup.
    None of these indexes enforce uniqueness, so legacy production data cannot
    make deployment fail because of historical duplicates.
    """
    indexes = {
        "users": [
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
            ([('quotation_number', 1)], "quotations_number"),
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
            ([('id', 1)], "sales_targets_id"),
            ([('sales_id', 1), ('year', 1)], "sales_targets_sales_year"),
            ([('year', 1), ('status', 1)], "sales_targets_year_status"),
            ([('is_demo', 1)], "sales_targets_demo"),
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
        for keys, name in collection_indexes:
            try:
                await collection.create_index(keys, name=name)
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
