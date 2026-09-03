import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("crm.db")

# 1. Ambil URL dari variabel Railway
mongodb_url = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
db_name = os.getenv("DB_NAME", "sales_crm_db")

# 2. Deklarasikan 'client' dan 'db' secara global agar rute lama tidak error
client = AsyncIOMotorClient(
    mongodb_url,
    maxPoolSize=50,
    minPoolSize=10,
    serverSelectionTimeoutMS=5000
)
db = client[db_name]

# 3. Fungsi untuk mengecek koneksi saat server menyala
async def connect_to_mongo():
    try:
        await client.admin.command('ping')
        logger.info(f"Berhasil terhubung ke MongoDB Atlas pada database: {db_name}")
    except Exception as e:
        logger.error(f"Gagal terhubung ke MongoDB: {e}")

async def close_mongo_connection():
    client.close()
    logger.info("Koneksi MongoDB ditutup.")
