from contextlib import asynccontextmanager
from pathlib import Path
import logging
import os

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from lib.db import connect_to_mongo, close_mongo_connection
from routers import auth, customers, pipeline, quotations, orders, activities, ai, admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("crm.server")
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
INDEX_FILE = FRONTEND_DIST / "index.html"

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect_to_mongo()
    except Exception:
        logger.exception("MongoDB startup check failed")
        # Keep the process alive so Railway health checks can report the service.
    yield
    await close_mongo_connection()

app = FastAPI(title="Sales CRM Production API", version="1.0.0", lifespan=lifespan)

raw_origins = os.getenv("CORS_ORIGINS", "").strip()
origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "sales-crm-management"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Terjadi kesalahan internal pada server."})

# Routers already declare their resource prefixes; mount the shared API prefix once.
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(customers.router, prefix=API_PREFIX)
app.include_router(pipeline.router, prefix=API_PREFIX)
app.include_router(quotations.router, prefix=API_PREFIX)
app.include_router(orders.router, prefix=API_PREFIX)
app.include_router(activities.router, prefix=API_PREFIX)
app.include_router(ai.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)

# Serve the built React SPA from the same origin in production.
if FRONTEND_DIST.exists():
    from fastapi.staticfiles import StaticFiles
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    # Never intercept API/docs/system paths.
    if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "health")):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return JSONResponse(status_code=404, content={"detail": "Frontend build not found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
