import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from passlib.context import CryptContext

from lib.db import db
from models.crm import LoginRequest, UserPublic
from routers.deps import current_user


router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


@router.post("/login", response_model=UserPublic)
async def login(
    payload: LoginRequest,
    response: Response
):
    email = str(payload.email).strip().lower()

    user = await db.users.find_one({
        "email": email
    })

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Email atau password salah"
        )

    password_hash = user.get("password_hash")

    if not password_hash:
        raise HTTPException(
            status_code=401,
            detail="Email atau password salah"
        )

    try:
        password_valid = pwd_context.verify(
            payload.password,
            password_hash
        )
    except Exception:
        password_valid = False

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Email atau password salah"
        )

    if user.get("status", "Active") != "Active":
        raise HTTPException(
            status_code=403,
            detail="User tidak aktif"
        )

    token = secrets.token_urlsafe(32)

    now = datetime.now(timezone.utc)

    await db.sessions.insert_one({
        "token": token,
        "user_id": user["id"],
        "created_at": now
    })

    await db.users.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "last_login": now
            }
        }
    )

    await db.audit_logs.insert_one({
        "id": secrets.token_hex(12),
        "user_name": user.get("name", ""),
        "action": "Login",
        "module": "Auth",
        "record_id": user["id"],
        "created_at": now
    })

    response.set_cookie(
        key="crm_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        secure=True
    )

    return UserPublic(
        **{
            **user,
            "last_login": now
        }
    )


@router.get("/me", response_model=UserPublic)
async def me(
    user: dict = Depends(current_user)
):
    return UserPublic(**user)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    crm_session: str | None = Cookie(default=None)
):
    if crm_session:
        await db.sessions.delete_one({
            "token": crm_session
        })

    response.delete_cookie(
        key="crm_session"
    )

    return Response(status_code=204)
