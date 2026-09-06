import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pymongo import MongoClient

# Inisialisasi Aplikasi FastAPI
app = FastAPI(title="Sales CRM Management API")

# Konfigurasi MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["CRM-Sales-Management"]

class CustomerModel(BaseModel):
    name: str
    email: str
    phone: str = None

@app.get("/api/health")
def health_check():
    try:
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
        db.customers.insert_one(customer.dict())
        return {"status": "success", "message": "Customer created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# MENYAJIKAN FRONTEND (REACT / VITE DIST)
# ==========================================

# Mencari folder dist di berbagai kemungkinan direktori Docker
dist_dir = None
possible_paths = ["dist", "../dist", "/app/backend/dist", "/app/dist", "./backend/dist"]

for path in possible_paths:
    if os.path.exists(path) and os.path.exists(os.path.join(path, "index.html")):
        dist_dir = path
        break

if dist_dir:
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        index_file = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend index.html not found."}
else:
    @app.get("/")
    def root_fallback():
        return {"message": "Sales CRM API is running. Frontend dist folder not found, please check Dockerfile copy path."}
