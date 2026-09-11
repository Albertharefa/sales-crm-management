from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from lib.db import db
from models.crm import UserPublic
from routers.common import audit, now
from routers.deps import require_roles

router = APIRouter(prefix="/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserUpdate(BaseModel):
    email: str | None = None
    name: str | None = None
    role: str | None = None
    manager_id: str | None = None
    phone: str | None = None
    status: str | None = None
    password: str | None = Field(default=None, min_length=8)


async def get_visible_user(user_id: str, current: dict) -> dict:
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if current.get("role") == "SUPER_ADMIN":
        return target

    if current.get("role") == "SALES_MANAGER":
        if target["id"] == current["id"] or target.get("manager_id") == current["id"]:
            return target

    raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke user ini")


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: str,
    user: dict = Depends(require_roles("SUPER_ADMIN", "SALES_MANAGER")),
):
    target = await get_visible_user(user_id, user)
    return UserPublic(**target)


@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    user: dict = Depends(require_roles("SUPER_ADMIN")),
):
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    updates = payload.model_dump(exclude_unset=True)

    if "email" in updates:
        email = (updates["email"] or "").strip().lower()
        if not email:
            raise HTTPException(status_code=400, detail="Email wajib diisi")
        existing = await db.users.find_one({"email": email, "id": {"$ne": user_id}})
        if existing:
            raise HTTPException(status_code=409, detail="Email sudah terdaftar")
        updates["email"] = email

    if "name" in updates and not (updates["name"] or "").strip():
        raise HTTPException(status_code=400, detail="Nama wajib diisi")

    if "role" in updates and updates["role"] not in ["SUPER_ADMIN", "SALES_MANAGER", "SALES"]:
        raise HTTPException(status_code=400, detail="Role tidak valid")

    if "manager_id" in updates and updates["manager_id"]:
        if updates["manager_id"] == user_id:
            raise HTTPException(status_code=400, detail="User tidak dapat menjadi manager dirinya sendiri")
        manager = await db.users.find_one({"id": updates["manager_id"], "role": "SALES_MANAGER"})
        if not manager:
            raise HTTPException(status_code=400, detail="Manager harus merupakan SALES_MANAGER")

    if "password" in updates:
        password = updates.pop("password")
        if password:
            updates["password_hash"] = pwd_context.hash(password)

    updates.pop("id", None)
    updates.pop("user_id", None)
    updates.pop("created_at", None)
    updates["updated_at"] = now()

    if updates:
        await db.users.update_one({"id": user_id}, {"$set": updates})

    updated = await db.users.find_one({"id": user_id})
    await audit(user, "Update", "Users", user_id, {"email": updated.get("email")})
    return UserPublic(**updated)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    user: dict = Depends(require_roles("SUPER_ADMIN")),
):
    if user_id == user.get("id"):
        raise HTTPException(status_code=400, detail="User yang sedang login tidak dapat dihapus")

    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count != 1:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    await audit(user, "Delete", "Users", user_id, {"email": target.get("email"), "name": target.get("name")})
    return {"message": "User berhasil dihapus", "id": user_id}
