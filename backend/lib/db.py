import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("crm.db")

# Support both legacy and Railway naming; MONGODB_URI takes precedence.
mongodb_url = os.getenv("MONGODB_URI") or os.getenv("MONGO_URL") or "mongodb://localhost:27017"
db_name = os.getenv("DB_NAME") or os.getenv("MONGO_DB_NAME") or "sales_crm_db"

client = AsyncIOMotorClient(
    mongodb_url,
    maxPoolSize=50,
    minPoolSize=5,
    serverSelectionTimeoutMS=5000,
)
db = client[db_name]

async def connect_to_mongo():
    await client.admin.command("ping")
    logger.info("MongoDB connection OK: %s", db_name)

async def close_mongo_connection():
    client.close()
    logger.info("MongoDB connection closed")
