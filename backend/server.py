import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext

from lib.db import db


# ============================================================
# PASSWORD
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ============================================================
# ADMIN BOOTSTRAP
# ============================================================

async def ensure_admin_user():
    """
    Automatically create the first CRM SUPER_ADMIN user
    from Railway environment variables:

        ADMIN_EMAIL
        ADMIN_PASSWORD
    """

    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "")

    if not admin_email or not admin_password:
        print(
            "INFO: ADMIN_EMAIL / ADMIN_PASSWORD not configured. "
            "Skipping admin bootstrap."
        )
        return

    if len(admin_password) < 8:
        print(
            "WARNING: ADMIN_PASSWORD must be at least 8 characters. "
            "Skipping admin bootstrap."
        )
        return

    try:
        existing = await db.users.find_one({
            "email": admin_email
        })

        if existing:
            print(
                f"INFO: Admin user already exists: {admin_email}"
            )
            return

        now = datetime.now(timezone.utc)

        admin_user = {
            "id": secrets.token_hex(16),
            "user_id": "USR-0001",
            "name": "Albert Wellkomputindo",
            "email": admin_email,
            "password_hash": pwd_context.hash(admin_password),
            "role": "SUPER_ADMIN",
            "manager_id": None,
            "phone": None,
            "status": "Active",
            "created_at": now,
            "last_login": None,
        }

        await db.users.insert_one(admin_user)

        print("=" * 60)
        print("CRM ADMIN USER CREATED")
        print(f"Email : {admin_email}")
        print("Role  : SUPER_ADMIN")
        print("=" * 60)

    except Exception as exc:
        print("=" * 60)
        print("WARNING: ADMIN BOOTSTRAP FAILED")
        print(f"Reason: {exc}")
        print("=" * 60)


# ============================================================
# DATABASE CHECK
# ============================================================

async def check_database():
    """
    Check MongoDB connection without preventing the API
    from starting if MongoDB is temporarily unavailable.
    """

    try:
        await db.command("ping")
        print("INFO: MongoDB connection OK")
        return True

    except Exception as exc:
        print("=" * 60)
        print("WARNING: MongoDB connection failed")
        print(f"Reason: {exc}")
        print("=" * 60)
        return False


# ============================================================
# STARTUP / SHUTDOWN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("=" * 60)
    print("CRM SALES MANAGEMENT API STARTING")
    print("=" * 60)

    # Check MongoDB
    database_ok = await check_database()

    if database_ok:
        # Create default SUPER_ADMIN if needed
        await ensure_admin_user()

    print("=" * 60)
    print("CRM API READY")
    print("=" * 60)

    yield

    print("CRM API SHUTDOWN")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Sales CRM Management",
    description="CRM Sales Management API",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    return {
        "status": "online",
        "application": "Sales CRM Management",
        "version": "1.0.0",
        "message": "Sales CRM API is running successfully",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    database_ok = await check_database()

    return {
        "status": "healthy" if database_ok else "degraded",
        "application": "Sales CRM Management",
        "database": "connected" if database_ok else "disconnected",
    }


# ============================================================
# ROUTERS
# ============================================================

# Core CRM routers
from routers.customers import router as customers_router
from routers.activities import router as activities_router
from routers.dashboard import router as dashboard_router
from routers.auth import router as auth_router
from routers.products import router as products_router
from routers.quotations import router as quotations_router
from routers.ai import router as ai_router

app.include_router(customers_router)
app.include_router(activities_router)
app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(quotations_router)
app.include_router(ai_router)


# ============================================================
# OPTIONAL / ADDITIONAL ROUTERS
# ============================================================

# These routers exist in the project structure shown in your
# screenshot. We load them separately so one optional module
# does not prevent the API from starting.

try:
    from routers.admin import router as admin_router

    app.include_router(admin_router)
    print("INFO: ✓ routers.admin")

except Exception as exc:
    print(f"WARNING: routers.admin not loaded: {exc}")


try:
    from routers.pipeline import router as pipeline_router

    app.include_router(pipeline_router)
    print("INFO: ✓ routers.pipeline")

except Exception as exc:
    print(f"WARNING: routers.pipeline not loaded: {exc}")


try:
    from routers.orders import router as orders_router

    app.include_router(orders_router)
    print("INFO: ✓ routers.orders")

except Exception as exc:
    print(f"WARNING: routers.orders not loaded: {exc}")


try:
    from routers.uploads import router as uploads_router

    app.include_router(uploads_router)
    print("INFO: ✓ routers.uploads")

except Exception as exc:
    print(f"WARNING: routers.uploads not loaded: {exc}")


# ============================================================
# ROUTER COUNT
# ============================================================

print("=" * 60)
print(f"Loaded routers: {len(app.routes)} routes")
print("CRM API READY")
print("=" * 60)
