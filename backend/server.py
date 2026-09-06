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

# Daftarkan semua rute API
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(customers.router, prefix="/api/v1/customers")
app.include_router(pipeline.router, prefix="/api/v1/pipeline")
app.include_router(quotations.router, prefix="/api/v1/quotations")
app.include_router(orders.router, prefix="/api/v1/orders")
app.include_router(activities.router, prefix="/api/v1/activities")
app.include_router(ai.router, prefix="/api/v1/ai")
app.include_router(admin.router, prefix="/api/v1/admin")

# Dashboard Utama dengan Menu Interaktif yang Bisa Diklik
@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard_home():
    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CRM Sales Management - Dashboard</title>
        <style>
            :root {
                --bg-sidebar: #0f172a;
                --bg-main: #f8fafc;
                --primary: #2563eb;
                --text-main: #1e293b;
                --card-bg: #ffffff;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                background-color: var(--bg-main);
                color: var(--text-main);
                display: flex;
                height: 100vh;
                overflow: hidden;
            }
            sidebar {
                width: 260px;
                background-color: var(--bg-sidebar);
                color: #94a3b8;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                padding: 20px;
            }
            .brand {
                color: white;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 30px;
                display: flex;
                flex-direction: column;
            }
            .brand span { font-size: 11px; color: #38bdf8; letter-spacing: 1px; }
            .menu-list { list-style: none; padding: 0; margin: 0; }
            .menu-list li {
                padding: 12px 15px;
                border-radius: 8px;
                margin-bottom: 5px;
                cursor: pointer;
                transition: 0.2s;
                color: #94a3b8;
            }
            .menu-list li:hover, .menu-list li.active {
                background-color: #1e293b;
                color: white;
            }
            .menu-list a {
                color: inherit;
                text-decoration: none;
                display: block;
            }
            main {
                flex: 1;
                padding: 30px;
                overflow-y: auto;
            }
            header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 25px;
            }
            h1 { margin: 0; font-size: 24px; color: #0f172a; }
            .subtitle { color: #64748b; font-size: 14px; margin-top: 5px; }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .card {
                background: var(--card-bg);
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border: 1px solid #e2e8f0;
            }
            .card-title { font-size: 12px; font-weight: bold; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
            .card-value { font-size: 28px; font-weight: bold; color: #0f172a; margin-top: 10px; }
            .actions-bar {
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                display: flex;
                gap: 15px;
                align-items: center;
            }
            .btn {
                background-color: var(--primary);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
                text-decoration: none;
                transition: background 0.2s;
            }
            .btn:hover { background-color: #1d4ed8; }
            .btn-secondary { background-color: #475569; }
            .btn-secondary:hover { background-color: #334155; }
        </style>
    </head>
    <body>
        <sidebar>
            <div>
                <div class="brand">
                    CRM Sales
                    <span>MANAGEMENT</span>
                </div>
                <ul class="menu-list">
                    <li class="active"><a href="/">📊 Dashboard</a></li>
                    <li><a href="/api/v1/customers/customers" target="_blank">👥 Customers (API)</a></li>
                    <li><a href="/api/v1/pipeline/" target="_blank">📈 Sales Pipeline</a></li>
                    <li><a href="/api/v1/quotations/" target="_blank">📝 Quotations</a></li>
                    <li><a href="/docs" target="_blank">⚙️ API Docs / Settings</a></li>
                </ul>
            </div>
            <div style="font-size: 12px; color: #64748b;">
                Status: <span style="color: #4ade80;">● Online</span>
            </div>
        </sidebar>

        <main>
            <header>
                <div>
                    <h1>Dashboard</h1>
                    <div class="subtitle">Ringkasan performa sales — terhubung langsung ke server Railway & MongoDB</div>
                </div>
            </header>

            <div class="grid">
                <div class="card">
                    <div class="card-title">Total Customer</div>
                    <div class="card-value" id="val-customers">1</div>
                </div>
                <div class="card">
                    <div class="card-title">Open Pipeline</div>
                    <div class="card-value" style="color: #2563eb;">Rp 4.2 M</div>
                </div>
                <div class="card">
                    <div class="card-title">Total Quotation</div>
                    <div class="card-value">30</div>
                </div>
                <div class="card">
                    <div class="card-title">Completed Orders</div>
                    <div class="card-value" style="color: #16a34a;">14</div>
                </div>
            </div>

            <div class="actions-bar">
                <a href="/docs" class="btn" target="_blank">Buka Dokumentasi API / Swagger</a>
                <a href="/api/v1/customers/customers" class="btn btn-secondary" target="_blank">Lihat Data Customers (JSON)</a>
            </div>
        </main>
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
