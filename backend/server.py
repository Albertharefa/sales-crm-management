from contextlib import asynccontextmanager
from pathlib import Path
import logging
import os
import secrets
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.staticfiles import StaticFiles

from lib.db import connect_to_mongo, close_mongo_connection, ensure_admin_user, db
from routers import auth, customers, pipeline, quotations, orders, activities, ai, admin, products, uploads, targets, users, password_reset, demo_data, integrity
from routers.dashboard import router as dashboard_router
from routers.order_monitoring import router as order_monitoring_router
from security.permissions import has_permission, permission_policy, normalize_role

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await ensure_admin_user()
    from seed_demo_data import seed_demo_data
    await seed_demo_data()
    yield
    await close_mongo_connection()


app = FastAPI(title="Sales CRM Production API", version="2.1.0", lifespan=lifespan)

configured_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,https://sales-crm-management-production.up.railway.app",
)
origins = [item.strip() for item in configured_origins.split(",") if item.strip()]
if "*" in origins:
    origins = ["http://localhost:5173", "http://localhost:3000", "https://sales-crm-management-production.up.railway.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rbac_middleware(request: Request, call_next):
    """Defense-in-depth authorization for every API request."""
    path = request.url.path
    if request.method == "OPTIONS":
        return await call_next(request)

    permission = permission_policy(path, request.method)
    if permission is not None:
        token = request.cookies.get("crm_session")
        user = None
        if token:
            session = await db.sessions.find_one({"token": token})
            if session:
                expires_at = session.get("expires_at")
                now = datetime.now(timezone.utc)
                if expires_at:
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    if expires_at > now:
                        user = await db.users.find_one({"id": session.get("user_id")})
                else:
                    user = await db.users.find_one({"id": session.get("user_id")})

        if not user:
            return JSONResponse(status_code=401, content={"detail": "Sesi tidak ditemukan atau telah berakhir"})
        if user.get("status", "Active") != "Active":
            return JSONResponse(status_code=401, content={"detail": "Pengguna tidak aktif"})

        role = normalize_role(user)
        allowed = permission == "__admin_only__" and role == "SUPER_ADMIN" or has_permission(user, permission)
        if not allowed:
            await db.audit_logs.insert_one({
                "id": secrets.token_hex(12),
                "user_id": user.get("id"),
                "user_name": user.get("name", ""),
                "action": "Access Denied",
                "module": "Security",
                "record_id": path,
                "details": {"method": request.method, "permission": permission, "role": role},
                "created_at": datetime.now(timezone.utc),
            })
            return JSONResponse(status_code=403, content={"detail": "Anda tidak memiliki izin untuk tindakan ini"})

    return await call_next(request)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, FastAPIHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)
    logging.exception("Unhandled error on %s", request.url.path, exc_info=exc)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Terjadi kesalahan internal pada server. Silakan coba lagi."})


app.include_router(auth.router, prefix="/api/v1")
app.include_router(password_reset.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(pipeline.router, prefix="/api/v1")
app.include_router(quotations.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(order_monitoring_router, prefix="/api/v1")
app.include_router(activities.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(demo_data.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")
app.include_router(targets.router, prefix="/api/v1")
app.include_router(integrity.router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health():
    try:
        await db.command("ping")
        return {"status": "ok", "database": "ok", "service": "sales-crm-management", "version": "2.1.0"}
    except Exception:
        logging.exception("Health check database ping failed")
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "unavailable", "service": "sales-crm-management", "version": "2.1.0"})


@app.get("/api/v1/health", tags=["system"])
async def api_health():
    return await health()


FRONTEND_DIST = Path("/app/frontend/dist")
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/", include_in_schema=False)
async def frontend_root():
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"status": "online", "message": "Frontend build belum tersedia"}, status_code=503)


@app.get("/{full_path:path}", include_in_schema=False)
async def frontend_spa(full_path: str):
    if full_path.startswith(("api/", "docs", "openapi.json", "health")):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"status": "online", "message": "Frontend build belum tersedia"}, status_code=503)
