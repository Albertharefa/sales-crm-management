import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pymongo import MongoClient

# Inisialisasi Aplikasi FastAPI
app = FastAPI(title="Sales CRM Management API")

# Konfigurasi MongoDB (Otomatis membaca environment variable Railway atau fallback ke koneksi lokal)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["CRM-Sales-Management"]

# Contoh Schema Pydantic untuk data sederhana
class CustomerModel(BaseModel):
    name: str
    email: str
    phone: str = None

# ==========================================
# API ROUTERS & ENDPOINTS
# ==========================================

@app.get("/api/health")
def health_check():
    try:
        # Cek koneksi database
        client.admin.command('ping')
        return {"status": "success", "message": "Sales CRM API is running and connected to MongoDB."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/customers")
def get_customers():
    try:
        customers = list(db.customers.find({}, {"_id": False}))
        return {"customers": customers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/customers")
def create_customer(customer: CustomerModel):
    try:
        result = db.customers.insert_one(customer.dict())
        return {"status": "success", "message": "Customer created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# MENYAJIKAN FRONTEND (REACT / VITE DIST)
# ==========================================

# Otomatis mendeteksi lokasi folder dist baik di dalam folder backend maupun di root utama
dist_path = None
for path in ["dist", "../dist", "backend/dist"]:
    if os.path.exists(path) and os.path.exists(os.path.join(path, "index.html")):
        dist_path = path
        break

if dist_path:
    assets_path = os.path.join(dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # Biarkan jalur yang diawali 'api' ditangani oleh router API di atas
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        index_file = os.path.join(dist_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend index.html not found."}
else:
    @app.get("/")
    def root_fallback():
        return {"message": "Sales CRM API is running. Frontend dist folder not found, please build the frontend."}
