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

# Path penghubung aman ke frontend
base_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dist = os.path.join(base_dir, "dist")
frontend_src = os.path.abspath(os.path.join(base_dir, "..", "frontend"))

target_dir = frontend_dist if os.path.exists(frontend_dist) else frontend_src

if os.path.exists(target_dir):
    if os.path.exists(os.path.join(target_dir, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(target_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")
        
        index_file = os.path.join(target_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        
        return {"message": "Sales CRM is active. Please check frontend assets."}
else:
    @app.get("/")
    def root():
        return {"message": "Sales CRM API is running successfully!"}
