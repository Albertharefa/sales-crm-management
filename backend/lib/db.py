import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

logger = logging.getLogger("crm.db")

# Support both Railway's preferred MONGODB_URI and the original project MONGO_URL.
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
        logger.info("MongoDB connection OK: %s", db_name)
    except Exception as exc:
        logger.error("MongoDB connection failed: %s", exc)
        raise


async def ensure_admin_user():
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")

    if not email or not password:
        logger.warning("ADMIN_EMAIL/ADMIN_PASSWORD not configured; admin auto-seed skipped")
        return

    existing = await db.users.find_one({"email": email})
    # Never perform password hashing/reset during application startup.
    # Production authentication can use ADMIN_PASSWORD explicitly via auth.py.
    if existing:
        return

    from datetime import datetime, timezone
    import uuid

    user = {
        "id": str(uuid.uuid4()),
        "user_id": "USR-ADMIN",
        "name": "Super Admin",
        "email": email,
        "role": "SUPER_ADMIN",
        "status": "Active",
        "password_hash": pwd_context.hash(password),
        "created_at": datetime.now(timezone.utc),
    }
    await db.users.insert_one(user)
    logger.info("CRM admin user auto-created: %s", email)


async def close_mongo_connection():
    client.close()
    logger.info("MongoDB connection closed")
