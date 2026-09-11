from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from lib.db import db
from routers.common import audit
from routers.deps import require_roles

router = APIRouter(prefix="/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8)


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    payload: PasswordResetRequest,
    user: dict = Depends(require_roles("SUPER_ADMIN")),
):
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    await db.users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": pwd_context.hash(payload.new_password)}},
    )
    await audit(user, "Reset Password", "Users", user_id, {"user_id": target.get("user_id", "")})
    return {"message": "Password berhasil di-reset"}
