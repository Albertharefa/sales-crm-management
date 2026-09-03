from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
import logging

from lib.db import connect_to_mongo, close_mongo_connection
# Impor router (pastikan path import sesuai struktur foldermu)
from routers import auth, customers, pipeline, quotations, orders, activities, ai, admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dijalankan saat server mulai (startup)
    await connect_to_mongo()
    yield
    # Dijalankan saat server dimatikan (shutdown)
    await close_mongo_connection()

app = FastAPI(
    title="Sales CRM Production API",
    version="1.0.0",
    lifespan=lifespan
)

# Konfigurasi CORS agar frontend Vercel/Netlify bisa berkomunikasi dengan backend ini
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tangani error global agar server tidak mati jika ada bug
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Error pada rute {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Terjadi kesalahan internal pada server. Silakan coba lagi."}
    )

# Daftarkan semua rute API
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(customers.router, prefix="/api/v1/customers")
app.include_router(pipeline.router, prefix="/api/v1/pipeline")
app.include_router(quotations.router, prefix="/api/v1/quotations")
app.include_router(orders.router, prefix="/api/v1/orders")
app.include_router(activities.router, prefix="/api/v1/activities")
app.include_router(ai.router, prefix="/api/v1/ai")
app.include_router(admin.router, prefix="/api/v1/admin")

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Sales CRM API is running."}

if __name__ == "__main__":
    # Server otomatis mendeteksi PORT yang diberikan oleh layanan hosting (Render/Railway)
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
