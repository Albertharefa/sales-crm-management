import os
from fastapi import FastAPI
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

@app.get("/")
def serve_frontend():
    index_file = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Sales CRM API is running successfully!"}
