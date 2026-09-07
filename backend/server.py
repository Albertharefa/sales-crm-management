from contextlib import asynccontextmanager
from pathlib import Path
import logging
import os

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext

from lib.db import connect_to_mongo, close_mongo_connection, db
from routers import auth, customers, pipeline, quotations, orders, activities, ai, admin
from routers.common import new_id, now

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("crm.server")

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
INDEX_FILE = FRONTEND_DIST / "index.html"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def ensure_admin():
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not email or not password:
        logger.warning("ADMIN_EMAIL/ADMIN_PASSWORD not set; admin auto-seed skipped")
        return
    existing = await db.users.find_one({"email": email})
    if existing:
        return
    await db.users.insert_one({
        "id": new_id(),
        "user_id": "USR-0001",
        "email": email,
        "name": os.getenv("ADMIN_NAME", "System Administrator"),
        "role": "SUPER_ADMIN",
        "status": "Active",
        "password_hash": pwd_context.hash(password),
        "created_at": now(),
    })
    logger.info("Initial SUPER_ADMIN user created: %s", email)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect_to_mongo()
        await ensure_admin()
    except Exception:
        logger.exception("MongoDB startup/seed check failed")
    yield
    await close_mongo_connection()

app = FastAPI(title="Sales CRM Production API", version="1.0.0", lifespan=lifespan)

raw_origins = os.getenv("CORS_ORIGINS", "").strip()
origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/health", tags=["system"])
async def health():
    try:
        await db.command("ping")
        return {"status": "ok", "database": "connected", "service": "sales-crm-management"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "unavailable", "service": "sales-crm-management"})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Terjadi kesalahan internal pada server."})

API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(customers.router, prefix=API_PREFIX)
app.include_router(pipeline.router, prefix=API_PREFIX)
app.include_router(quotations.router, prefix=API_PREFIX)
app.include_router(orders.router, prefix=API_PREFIX)
app.include_router(activities.router, prefix=API_PREFIX)
app.include_router(ai.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)

if FRONTEND_DIST.exists():
    from fastapi.staticfiles import StaticFiles
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "health")):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return JSONResponse(status_code=404, content={"detail": "Frontend build not found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
