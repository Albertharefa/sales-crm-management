import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from passlib.context import CryptContext

from lib.db import db
from models.crm import LoginRequest, UserPublic
from routers.deps import current_user
from security.permissions import ROLES, permissions_for_role

router = APIRouter(tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SESSION_TTL_SECONDS = 60 * 60 * 8
MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15


def _utc(value):
    if not value:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def _audit_auth(user: dict | None, action: str, record_id: str | None = None, details: dict | None = None):
    await db.audit_logs.insert_one({
        "id": secrets.token_hex(12),
        "user_name": (user or {}).get("name", "Unknown"),
        "user_id": (user or {}).get("id"),
        "action": action,
        "module": "Auth",
        "record_id": record_id,
        "details": details or {},
        "created_at": datetime.now(timezone.utc),
    })


@router.post("/login", response_model=UserPublic)
async def login(payload: LoginRequest, response: Response):
    identifier = str(payload.email).strip().lower()
    user = await db.users.find_one({
        "$or": [
            {"email": identifier},
            {"user_id": identifier.upper()},
        ]
    })
    if not user:
        raise HTTPException(status_code=401, detail="Email/User ID atau password salah")

    now = datetime.now(timezone.utc)
    locked_until = _utc(user.get("locked_until"))
    if locked_until and locked_until > now:
        remaining = max(1, int((locked_until - now).total_seconds() // 60) + 1)
        raise HTTPException(status_code=423, detail=f"Akun terkunci sementara. Coba lagi dalam {remaining} menit")

    if user.get("status", "Active") != "Active":
        await _audit_auth(user, "Login Denied", user.get("id"), {"reason": "Inactive user"})
        raise HTTPException(status_code=403, detail="User tidak aktif")

    role = str(user.get("role") or "").strip().upper()
    if role not in ROLES:
        await _audit_auth(user, "Login Denied", user.get("id"), {"reason": "Invalid role"})
        raise HTTPException(status_code=403, detail="Role pengguna tidak valid")

    password_valid = False
    password_hash = user.get("password_hash")
    if password_hash:
        try:
            password_valid = pwd_context.verify(payload.password, password_hash)
        except Exception:
            password_valid = False

    force_env_admin = (
        os.getenv("ADMIN_FORCE_PASSWORD_RESET", "false").strip().lower() in {"1", "true", "yes", "on"}
        and identifier in {os.getenv("ADMIN_EMAIL", "").strip().lower(), str(user.get("user_id") or "").lower()}
        and bool(os.getenv("ADMIN_PASSWORD", ""))
        and secrets.compare_digest(payload.password, os.getenv("ADMIN_PASSWORD", ""))
    )
    if force_env_admin:
        password_valid = True

    if not password_valid:
        failed = int(user.get("failed_login_attempts", 0) or 0) + 1
        updates = {"failed_login_attempts": failed, "last_failed_login": now}
        if failed >= MAX_FAILED_LOGINS:
            updates["locked_until"] = now + timedelta(minutes=LOCK_MINUTES)
            updates["failed_login_attempts"] = 0
            await _audit_auth(user, "Login Locked", user.get("id"), {"lock_minutes": LOCK_MINUTES})
        else:
            await _audit_auth(user, "Login Failed", user.get("id"), {"attempt": failed})
        await db.users.update_one({"id": user["id"]}, {"$set": updates})
        raise HTTPException(status_code=401, detail="Email/User ID atau password salah")

    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"failed_login_attempts": 0, "locked_until": None, "last_login": now}},
    )

    token = secrets.token_urlsafe(48)
    expires_at = now + timedelta(seconds=SESSION_TTL_SECONDS)
    await db.sessions.insert_one({
        "token": token,
        "user_id": user["id"],
        "created_at": now,
        "expires_at": expires_at,
        "last_seen_at": now,
    })

    await _audit_auth(user, "Login Success", user["id"], {"role": role})

    secure_cookie = os.getenv("COOKIE_SECURE", "true").strip().lower() in {"1", "true", "yes", "on"}
    response.set_cookie(
        key="crm_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
        secure=secure_cookie,
        path="/",
    )
    return UserPublic(**{**user, "last_login": now})


@router.get("/me", response_model=UserPublic)
async def me(user: dict = Depends(current_user)):
    return UserPublic(**user)


@router.get("/session-info")
async def session_info(user: dict = Depends(current_user)):
    role = str(user.get("role") or "").strip().upper()
    return {
        "authenticated": True,
        "role": role,
        "permissions": permissions_for_role(role),
        "session_ttl_seconds": SESSION_TTL_SECONDS,
    }


@router.post("/logout", status_code=204)
async def logout(response: Response, crm_session: str | None = Cookie(default=None)):
    if crm_session:
        session = await db.sessions.find_one({"token": crm_session})
        if session:
            user = await db.users.find_one({"id": session.get("user_id")})
            await _audit_auth(user, "Logout", session.get("user_id"))
        await db.sessions.delete_one({"token": crm_session})
    response.delete_cookie(key="crm_session", path="/")
    return Response(status_code=204)
