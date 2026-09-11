from datetime import datetime, timezone
from typing import Any

from fastapi import Cookie, Depends, HTTPException
from lib.db import db
from security.permissions import ROLES, has_permission

SESSION_TTL_SECONDS = 60 * 60 * 8


async def current_user(crm_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    if not crm_session:
        raise HTTPException(status_code=401, detail="Sesi tidak ditemukan")

    session = await db.sessions.find_one({"token": crm_session})
    if not session:
        raise HTTPException(status_code=401, detail="Sesi tidak valid")

    now = datetime.now(timezone.utc)
    expires_at = session.get("expires_at")
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            await db.sessions.delete_one({"token": crm_session})
            raise HTTPException(status_code=401, detail="Sesi telah berakhir. Silakan login kembali")
    else:
        created_at = session.get("created_at")
        if created_at:
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if (now - created_at).total_seconds() > SESSION_TTL_SECONDS:
                await db.sessions.delete_one({"token": crm_session})
                raise HTTPException(status_code=401, detail="Sesi telah berakhir. Silakan login kembali")

    user = await db.users.find_one({"id": session["user_id"]})
    if not user or user.get("status", "Active") != "Active":
        await db.sessions.delete_one({"token": crm_session})
        raise HTTPException(status_code=401, detail="Pengguna tidak aktif")

    role = str(user.get("role") or "").strip().upper()
    if role not in ROLES:
        await db.sessions.delete_one({"token": crm_session})
        raise HTTPException(status_code=403, detail="Role pengguna tidak valid")

    # Keep the session alive for active users, but never beyond the fixed TTL
    # unless the login endpoint creates a fresh session.
    await db.sessions.update_one(
        {"token": crm_session},
        {"$set": {"last_seen_at": now}},
    )
    return user


def require_roles(*roles: str):
    normalized = {str(role).strip().upper() for role in roles}

    async def dependency(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        if str(user.get("role") or "").strip().upper() not in normalized:
            raise HTTPException(status_code=403, detail="Anda tidak memiliki izin")
        return user

    return dependency


def require_permission(permission: str):
    async def dependency(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        if not has_permission(user, permission):
            raise HTTPException(status_code=403, detail="Anda tidak memiliki izin untuk tindakan ini")
        return user

    return dependency
