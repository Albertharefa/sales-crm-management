from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from lib.db import db
from models.crm import UploadResponse
from routers.common import new_id
from routers.deps import current_user

router = APIRouter(prefix="/uploads", tags=["uploads"])
ALLOWED = {"application/pdf", "image/jpeg", "image/png", "text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}


@router.post("", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...), user: dict = Depends(current_user)):
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=415, detail="Format file tidak didukung")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Ukuran file maksimum 10MB")
    doc = {"id": new_id(), "file_name": file.filename or "upload", "content_type": file.content_type, "content": content, "size": len(content), "uploaded_by": user["id"], "created_at": datetime.now(timezone.utc)}
    await db.documents.insert_one(doc)
    return UploadResponse(id=doc["id"], file_name=doc["file_name"], content_type=doc["content_type"], size=doc["size"], url=f"/api/v1/uploads/{doc['id']}")


@router.get("/{file_id}")
async def download_file(file_id: str, user: dict = Depends(current_user)):
    from fastapi.responses import Response
    doc = await db.documents.find_one({"id": file_id})
    if not doc:
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    return Response(doc["content"], media_type=doc["content_type"], headers={"Content-Disposition": f"attachment; filename={doc['file_name']}"})