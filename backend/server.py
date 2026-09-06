from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
import logging

from lib.db import connect_to_mongo, close_mongo_connection
from routers import auth, customers, pipeline, quotations, orders, activities, ai, admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(
    title="Sales CRM Production API",
    version="1.0.0",
    lifespan=lifespan
)

origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Error pada rute {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Terjadi kesalahan internal pada server. Silakan coba lagi."}
    )

# Daftarkan semua rute API yang sudah ada
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(customers.router, prefix="/api/v1/customers")
app.include_router(pipeline.router, prefix="/api/v1/pipeline")
app.include_router(quotations.router, prefix="/api/v1/quotations")
app.include_router(orders.router, prefix="/api/v1/orders")
app.include_router(activities.router, prefix="/api/v1/activities")
app.include_router(ai.router, prefix="/api/v1/ai")
app.include_router(admin.router, prefix="/api/v1/admin")

# Tampilan Halaman Utama (Dashboard Web Langsung Muncul)
@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def root():
    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sales CRM Management</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                height: 100vh;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                color: white;
            }
            .card {
                background: rgba(255, 255, 255, 0.1);
                padding: 40px;
                border-radius: 16px;
                backdrop-filter: blur(12px);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                text-align: center;
                max-width: 450px;
                width: 90%;
            }
            h1 { margin-bottom: 10px; font-size: 26px; }
            p { color: #e2e8f0; font-size: 15px; margin-bottom: 25px; }
            .btn {
                display: inline-block;
                background: #10b981;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                transition: background 0.3s;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
            }
            .btn:hover { background: #059669; }
            .status {
                margin-top: 20px;
                font-size: 13px;
                color: #93c5fd;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Sales CRM Management</h1>
            <p>Sistem backend dan database MongoDB Anda sudah terhubung dan aktif sepenuhnya di Railway!</p>
            <a href="/docs" class="btn">Buka Dokumentasi API / Docs</a>
            <div class="status">● Status: Live & Ready to Use</div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
