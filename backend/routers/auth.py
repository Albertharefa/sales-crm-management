import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from passlib.context import CryptContext
from lib.db import db
from models.crm import LoginRequest, UserPublic
from routers.deps import current_user

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/login", response_model=UserPublic)
async def login(payload: LoginRequest, response: Response):
    user = await db.users.find_one({"email": payload.email.lower()})
    if not user or not pwd_context.verify(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Email atau password salah")
    token = secrets.token_urlsafe(32)
    await db.sessions.insert_one({"token": token, "user_id": user["id"], "created_at": datetime.now(timezone.utc)})
    await db.users.update_one({"id": user["id"]}, {"$set": {"last_login": datetime.now(timezone.utc)}})
    await db.audit_logs.insert_one({"id": secrets.token_hex(12), "user_name": user["name"], "action": "Login", "module": "Auth", "record_id": user["id"], "created_at": datetime.now(timezone.utc)})
    response.set_cookie("crm_session", token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 7)
    return UserPublic(**{**user, "last_login": datetime.now(timezone.utc)})


@router.get("/me", response_model=UserPublic)
async def me(user: dict = Depends(current_user)):
    return UserPublic(**user)


@router.post("/logout", status_code=204)
async def logout(response: Response, crm_session: str | None = Cookie(default=None)):
    if crm_session:
        await db.sessions.delete_one({"token": crm_session})
    response.delete_cookie("crm_session")