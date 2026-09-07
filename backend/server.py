from contextlib import asynccontextmanager
from pathlib import Path
import logging
import os

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from lib.db import connect_to_mongo, close_mongo_connection, ensure_admin_user
from routers import auth, customers, pipeline, quotations, orders, activities, ai, admin, products, uploads
from routers.dashboard import router as dashboard_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await ensure_admin_user()
    yield
    await close_mongo_connection()

app = FastAPI(
    title="Sales CRM Production API",
    version="2.0.0",
    lifespan=lifespan,
)

configured_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,"
    "https://sales-crm-management-production.up.railway.app",
)
origins = [item.strip() for item in configured_origins.split(",") if item.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled error on %s", request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Terjadi kesalahan internal pada server. Silakan coba lagi."},
    )

# All application APIs live under one stable versioned prefix.
app.include_router(auth.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(pipeline.router, prefix="/api/v1")
app.include_router(quotations.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(activities.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")

@app.get("/health", tags=["system"])
async def health():
    return {
        "status": "ok",
        "service": "sales-crm-management",
        "version": "2.0.0",
    }

@app.get("/api/v1/health", tags=["system"])
async def api_health():
    return await health()

FRONTEND_DIST = Path("/app/frontend/dist")

if FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets",
    )

@app.get("/", include_in_schema=False)
async def frontend_root():
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse(
        {"status": "online", "message": "Frontend build belum tersedia"},
        status_code=503,
    )

@app.get("/{full_path:path}", include_in_schema=False)
async def frontend_spa(full_path: str):
    # Never intercept API paths.
    if full_path.startswith(("api/", "docs", "openapi.json", "health")):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse(
        {"status": "online", "message": "Frontend build belum tersedia"},
        status_code=503,
    )
