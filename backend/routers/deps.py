from datetime import datetime, timezone
from typing import Any
import time

from fastapi import Cookie, Depends, HTTPException
from lib.db import db
from security.permissions import ROLES, has_permission

SESSION_TTL_SECONDS = 60 * 60 * 8
AUTH_CACHE_TTL_SECONDS = 15

# Small in-process cache shared by the RBAC middleware and FastAPI dependencies.
# Before this, one protected request could query the same session and user more
# than once and also write last_seen_at on every request. That added avoidable
# MongoDB round-trips to every CRM menu.
_auth_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def invalidate_session_cache(token: str | None = None) -> None:
    if token:
        _auth_cache.pop(token, None)
    else:
        _auth_cache.clear()


def _purge_expired_cache(now_monotonic: float) -> None:
    if len(_auth_cache) < 128:
        return
    expired = [
        token for token, (cached_until, _user) in _auth_cache.items()
        if cached_until <= now_monotonic
    ]
    for token in expired:
        _auth_cache.pop(token, None)


async def get_authenticated_user(crm_session: str | None) -> dict[str, Any]:
    """Authenticate a session with a short TTL cache.

    The session expiry is still enforced against the cached session data, while
    the short cache prevents repeated session/user reads during normal page
    navigation. Logout/password changes explicitly invalidate the cache.
    """
    if not crm_session:
        raise HTTPException(status_code=401, detail="Sesi tidak ditemukan")

    now_monotonic = time.monotonic()
    _purge_expired_cache(now_monotonic)

    cached = _auth_cache.get(crm_session)
    if cached and cached[0] > now_monotonic:
        return cached[1]

    session = await db.sessions.find_one(
        {"token": crm_session},
        {"_id": 0, "token": 1, "user_id": 1, "created_at": 1, "expires_at": 1},
    )
    if not session:
        invalidate_session_cache(crm_session)
        raise HTTPException(status_code=401, detail="Sesi tidak valid")

    now = datetime.now(timezone.utc)
    expires_at = session.get("expires_at")
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            invalidate_session_cache(crm_session)
            await db.sessions.delete_one({"token": crm_session})
            raise HTTPException(status_code=401, detail="Sesi telah berakhir. Silakan login kembali")
    else:
        created_at = session.get("created_at")
        if created_at:
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if (now - created_at).total_seconds() > SESSION_TTL_SECONDS:
                invalidate_session_cache(crm_session)
                await db.sessions.delete_one({"token": crm_session})
                raise HTTPException(status_code=401, detail="Sesi telah berakhir. Silakan login kembali")

    user = await db.users.find_one({"id": session["user_id"]})
    if not user or user.get("status", "Active") != "Active":
        invalidate_session_cache(crm_session)
        await db.sessions.delete_one({"token": crm_session})
        raise HTTPException(status_code=401, detail="Pengguna tidak aktif")

    role = str(user.get("role") or "").strip().upper()
    if role not in ROLES:
        invalidate_session_cache(crm_session)
        await db.sessions.delete_one({"token": crm_session})
        raise HTTPException(status_code=403, detail="Role pengguna tidak valid")

    _auth_cache[crm_session] = (
        now_monotonic + AUTH_CACHE_TTL_SECONDS,
        user,
    )
    return user


async def current_user(crm_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    return await get_authenticated_user(crm_session)


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
