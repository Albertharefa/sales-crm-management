from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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

# Daftarkan rute API
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(customers.router, prefix="/api/v1/customers")
app.include_router(pipeline.router, prefix="/api/v1/pipeline")
app.include_router(quotations.router, prefix="/api/v1/quotations")
app.include_router(orders.router, prefix="/api/v1/orders")
app.include_router(activities.router, prefix="/api/v1/activities")
app.include_router(ai.router, prefix="/api/v1/ai")
app.include_router(admin.router, prefix="/api/v1/admin")

# Mengarahkan langsung ke tampilan frontend React
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.exists(frontend_path):
    if os.path.exists(os.path.join(frontend_path, "public")):
        app.mount("/public", StaticFiles(directory=os.path.join(frontend_path, "public")), name="public")

    @app.get("/{full_path:path}", tags=["Frontend"])
    def serve_frontend(full_path: str):
        if full_path.startswith("api") or full_path == "docs" or full_path == "openapi.json":
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")
        
        index_file = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Frontend index.html not found"}
else:
    @app.get("/", tags=["Root"])
    async def root():
        return {"message": "Sales CRM API is running."}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
