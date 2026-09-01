async def ensure_admin_user():
    """
    Ensure the CRM SUPER_ADMIN exists and always uses
    the password configured in Railway ADMIN_PASSWORD.
    """

    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "")

    if not admin_email or not admin_password:
        print(
            "INFO: ADMIN_EMAIL / ADMIN_PASSWORD not configured. "
            "Skipping admin bootstrap."
        )
        return

    if len(admin_password) < 8:
        print(
            "WARNING: ADMIN_PASSWORD must be at least 8 characters. "
            "Skipping admin bootstrap."
        )
        return

    try:
        existing = await db.users.find_one({
            "email": admin_email
        })

        password_hash = pwd_context.hash(admin_password)
        now = datetime.now(timezone.utc)

        if existing:
            await db.users.update_one(
                {"id": existing["id"]},
                {
                    "$set": {
                        "password_hash": password_hash,
                        "role": "SUPER_ADMIN",
                        "status": "Active",
                        "name": existing.get(
                            "name",
                            "Albert Wellkomputindo"
                        ),
                    }
                }
            )

            print("=" * 60)
            print("CRM ADMIN USER PASSWORD UPDATED")
            print(f"Email : {admin_email}")
            print("Role  : SUPER_ADMIN")
            print("=" * 60)

            return

        admin_user = {
            "id": secrets.token_hex(16),
            "user_id": "USR-0001",
            "name": "Albert Wellkomputindo",
            "email": admin_email,
            "password_hash": password_hash,
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

    except Exception as exc:
        print("=" * 60)
        print("WARNING: ADMIN BOOTSTRAP FAILED")
        print(f"Reason: {exc}")
        print("=" * 60)
