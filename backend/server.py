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
from lib import custom_customer_patch
from routers.dashboard import router as dashboard_router
from routers.order_monitoring import router as order_monitoring_router
from routers.deps import get_authenticated_user
from security.permissions import has_permission, permission_policy, normalize_role

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


async def _safe_demo_targets(sales: list[dict]) -> None:
    """Ensure the legacy demo seed cannot create monthly duplicates.

    Production target integrity is annual: one sales_id + one year = one target.
    The legacy seed attempted 12 monthly documents and now conflicts with the
    unique annual constraint. Keep exactly one demo annual target for the first
    active sales user without touching non-demo production targets.
    """
    if not sales:
        return
    sales_user = sales[0]
    year = datetime.now(timezone.utc).year
    existing = await db.sales_targets.find_one(
        {"is_demo": True, "sales_id": sales_user["id"], "year": year},
        {"_id": 0, "id": 1},
    )
    if existing:
        return
    await db.sales_targets.insert_one({
        "id": secrets.token_hex(12),
        "sales_id": sales_user["id"],
        "sales_name": sales_user["name"],
        "year": year,
        "target": 500000000.0,
        "is_demo": True,
        "demo_label": "CRM UI demo data",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })


def _demo_seed_enabled() -> bool:
    return os.getenv("SEED_DEMO_DATA", "false").strip().lower() in {"1", "true", "yes", "on"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await ensure_admin_user()
    if _demo_seed_enabled():
        import seed_demo_data as demo_seed
        original_ensure_targets = demo_seed._ensure_targets
        demo_seed._ensure_targets = _safe_demo_targets
        try:
            await demo_seed.seed_demo_data()
        finally:
            demo_seed._ensure_targets = original_ensure_targets
    else:
        logging.info("CRM demo seed disabled (SEED_DEMO_DATA=false)")
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
        try:
            user = await get_authenticated_user(token)
        except FastAPIHTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)

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


@app.get("/wellracom-logo.svg", include_in_schema=False)
async def frontend_wellracom_logo():
    logo = FRONTEND_DIST / "wellracom-logo.svg"
    if logo.exists():
        return FileResponse(logo, media_type="image/svg+xml")
    return JSONResponse({"detail": "Logo Wellracom tidak ditemukan"}, status_code=404)


@app.get("/wellracom-crm-logo.svg", include_in_schema=False)
async def frontend_logo():
    logo = FRONTEND_DIST / "wellracom-crm-logo.svg"
    if logo.exists():
        return FileResponse(logo, media_type="image/svg+xml")
    return JSONResponse({"detail": "Logo tidak ditemukan"}, status_code=404)


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