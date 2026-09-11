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
    # Non-unique indexes are safe against legacy duplicate data and materially
    # improve authentication, RBAC, audit, and list-query performance.
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
