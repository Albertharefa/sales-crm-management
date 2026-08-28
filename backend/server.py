from contextlib import asynccontextmanager
from pathlib import Path
import logging
import os
from fastapi import APIRouter, FastAPI
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from lib.db import client, db

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    client.close()


app = FastAPI(title="CRM Sales Management Production", lifespan=lifespan)
api_router = APIRouter(prefix="/api")

from routers.auth import router as auth_router
from routers.customers import router as customers_router
from routers.pipeline import router as pipeline_router
from routers.activities import router as activities_router
from routers.products import router as products_router
from routers.quotations import router as quotations_router
from routers.orders import router as orders_router
from routers.dashboard import router as dashboard_router
from routers.admin import router as admin_router
from routers.uploads import router as uploads_router

api_router.include_router(auth_router)
api_router.include_router(customers_router)
api_router.include_router(pipeline_router)
api_router.include_router(activities_router)
api_router.include_router(products_router)
api_router.include_router(quotations_router)
api_router.include_router(orders_router)
api_router.include_router(dashboard_router)
api_router.include_router(admin_router)
api_router.include_router(uploads_router)

@api_router.get("/")
async def root():
    return {"message": "CRM Sales Management API", "status": "ready"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","), allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router)