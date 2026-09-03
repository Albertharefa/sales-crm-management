import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("crm.db")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    # Mengambil MONGODB_URI dari environment (misal dari Railway/Render), jika tidak ada gunakan localhost
    mongodb_url = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    # Mengambil nama database, default ke sales_crm_db
    db_name = os.getenv("DB_NAME", "sales_crm_db")
    
    logger.info(f"Connecting to MongoDB database: {db_name} at {mongodb_url.split('@')[-1] if '@' in mongodb_url else mongodb_url}")
    
    try:
        db_instance.client = AsyncIOMotorClient(
            mongodb_url,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000
        )
        db_instance.db = db_instance.client[db_name]
        # Test koneksi dengan ping
        await db_instance.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB Atlas/Production.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed.")

def get_db():
    if db_instance.db is None:
        raise Exception("Database is not initialized. Please call connect_to_mongo() first.")
    return db_instance.db
