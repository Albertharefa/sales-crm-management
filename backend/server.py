from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import importlib

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("sales-crm")

# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Sales CRM Management",
    description="Sales CRM Management API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "sales-crm-management",
    }


# ============================================================
# API STATUS
# ============================================================

@app.get("/api")
async def api_status():
    return {
        "status": "online",
        "message": "Sales CRM API is running",
    }


# ============================================================
# LOAD EXISTING ROUTERS SAFELY
# ============================================================

def load_router(module_name: str, router_name: str = "router"):
    """
    Load an existing FastAPI router without crashing the
    entire application if the module is missing or broken.
    """

    try:
        module = importlib.import_module(module_name)
        router = getattr(module, router_name, None)

        if router is None:
            logger.warning(
                "Router ditemukan tetapi attribute '%s' tidak ada: %s",
                router_name,
                module_name,
            )
            return False

        app.include_router(router)

        logger.info(
            "Router berhasil dimuat: %s.%s",
            module_name,
            router_name,
        )

        return True

    except ModuleNotFoundError as e:
        logger.warning(
            "Router tidak ditemukan: %s | %s",
            module_name,
            e,
        )
        return False

    except Exception as e:
        logger.exception(
            "Router gagal dimuat: %s | %s",
            module_name,
            e,
        )
        return False


# ============================================================
# EXISTING CRM ROUTERS
# ============================================================

ROUTERS = [
    # Customers
    ("routers.customers", "router"),

    # Customer
    ("routers.customer", "router"),

    # Leads
    ("routers.leads", "router"),

    # Sales
    ("routers.sales", "router"),

    # Opportunities
    ("routers.opportunities", "router"),

    # Activities
    ("routers.activities", "router"),

    # Dashboard
    ("routers.dashboard", "router"),

    # Authentication
    ("routers.auth", "router"),

    # Users
    ("routers.users", "router"),

    # Products
    ("routers.products", "router"),

    # Quotations
    ("routers.quotations", "router"),

    # Reports
    ("routers.reports", "router"),

    # AI
    ("routers.ai", "router"),
]


loaded_routers = []

for module_name, router_name in ROUTERS:
    if load_router(module_name, router_name):
        loaded_routers.append(module_name)


# ============================================================
# ROUTER STATUS
# ============================================================

@app.get("/api/status")
async def api_detailed_status():
    return {
        "status": "online",
        "application": "Sales CRM Management",
        "loaded_routers": loaded_routers,
        "router_count": len(loaded_routers),
    }


# ============================================================
# GLOBAL ERROR HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception(
        "Unhandled application error: %s",
        exc,
    )

    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Application encountered an unexpected error.",
        },
    )


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("SALES CRM MANAGEMENT STARTING")
    logger.info("=" * 60)

    logger.info(
        "Environment: %s",
        os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
    )

    logger.info(
        "Port: %s",
        os.getenv("PORT", "8080"),
    )

    logger.info(
        "Loaded routers: %s",
        len(loaded_routers),
    )

    for router in loaded_routers:
        logger.info("  ✓ %s", router)

    logger.info("=" * 60)
    logger.info("CRM API READY")
    logger.info("=" * 60)


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
