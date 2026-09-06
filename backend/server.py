import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
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

# Serve Frontend jika ada, atau fallback pesan API
dist_path = os.path.join(os.path.dirname(__file__), "dist")
if os.path.exists(dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")
        index_file = os.path.join(dist_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Frontend index.html missing"}
else:
    @app.get("/")
    def root():
        return {"message": "Sales CRM API is running successfully!"}
