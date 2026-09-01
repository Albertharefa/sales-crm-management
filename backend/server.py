import os
import secrets
from datetime import datetime, timezone

from passlib.context import CryptContext

from lib.db import db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def ensure_admin_user():
    """
    Create the first CRM admin user automatically if it does not exist.
    Credentials are taken from Railway environment variables:
      ADMIN_EMAIL
      ADMIN_PASSWORD
    """

    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "")

    if not admin_email or not admin_password:
        print("INFO: ADMIN_EMAIL / ADMIN_PASSWORD not configured. Skipping admin bootstrap.")
        return

    if len(admin_password) < 8:
        print("WARNING: ADMIN_PASSWORD must be at least 8 characters.")
        return

    existing = await db.users.find_one({"email": admin_email})

    if existing:
        print(f"INFO: Admin user already exists: {admin_email}")
        return

    now = datetime.now(timezone.utc)

    admin_user = {
        "id": secrets.token_hex(16),
        "user_id": "USR-0001",
        "name": "Albert Wellkomputindo",
        "email": admin_email,
        "password_hash": pwd_context.hash(admin_password),
        "role": "SUPER_ADMIN",
        "manager_id": None,
        "phone": None,
        "status": "Active",
        "created_at": now,
        "last_login": None,
    }

    await db.users.insert_one(admin_user)

    print("=" * 60)
    print("CRM ADMIN USER CREATED")
    print(f"Email : {admin_email}")
    print("Role  : SUPER_ADMIN")
    print("=" * 60)
