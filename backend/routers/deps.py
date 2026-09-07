from typing import Any
from fastapi import Cookie, Depends, HTTPException
from lib.db import db


async def current_user(crm_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    if not crm_session:
        raise HTTPException(status_code=401, detail="Sesi tidak ditemukan")
    session = await db.sessions.find_one({"token": crm_session})
    if not session:
        raise HTTPException(status_code=401, detail="Sesi tidak valid")
    user = await db.users.find_one({"id": session["user_id"]})
    if not user or user.get("status") != "Active":
        raise HTTPException(status_code=401, detail="Pengguna tidak aktif")
    return user


def require_roles(*roles: str):
    async def dependency(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Anda tidak memiliki izin")
        return user

    return dependency
