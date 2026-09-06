import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pymongo import MongoClient

app = FastAPI(title="Sales CRM Management API")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["CRM-Sales-Management"]

@app.get("/api/health")
def health_check():
    try:
        client.admin.command('ping')
        return {"status": "success", "message": "Sales CRM API is running."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Konfigurasi agar FastAPI membaca file statis frontend
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
dist_path = os.path.join(os.path.dirname(__file__), "dist")

# Cek apakah folder dist ada di backend atau root frontend
target_static = dist_path if os.path.exists(dist_path) else frontend_path

if os.path.exists(target_static):
    if os.path.exists(os.path.join(target_static, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(target_static, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Cari file index.html
        index_file = os.path.join(target_static, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        
        return {"message": "Sales CRM Frontend file not found, please check deployment path."}
else:
    @app.get("/")
    def root():
        return {"message": "Sales CRM API is running successfully!"}
