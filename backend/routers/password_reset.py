import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from services.password_reset import create_reset_request, reset_password

router = APIRouter(prefix="/auth", tags=["auth"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=8, max_length=128)


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    try:
        await create_reset_request(str(payload.email).strip().lower())
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Layanan email reset password belum tersedia. Silakan hubungi administrator CRM.") from exc

    return {"message": "Jika email terdaftar, link reset password telah dikirim ke email tersebut."}


@router.post("/reset-password")
async def reset_password_endpoint(payload: ResetPasswordRequest):
    if not re.search(r"[A-Za-z]", payload.password) or not re.search(r"\d", payload.password):
        raise HTTPException(status_code=400, detail="Password baru harus memiliki minimal 8 karakter dan mengandung huruf serta angka.")

    success = await reset_password(payload.token, payload.password)
    if not success:
        raise HTTPException(status_code=400, detail="Link reset password tidak valid atau sudah kedaluwarsa.")

    return {"message": "Password berhasil direset. Silakan login dengan password baru."}
