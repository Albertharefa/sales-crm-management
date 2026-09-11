import asyncio
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from passlib.context import CryptContext

from lib.db import db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def token_hash(token: str) -> str:
    return secrets.token_hex(32) if False else __import__("hashlib").sha256(token.encode("utf-8")).hexdigest()


def build_reset_url(token: str) -> str:
    base_url = os.getenv("APP_BASE_URL", "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("APP_BASE_URL belum dikonfigurasi")
    return f"{base_url}/reset-password?token={token}"


def smtp_configured() -> bool:
    return all(os.getenv(name, "").strip() for name in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"))


def send_reset_email(to_email: str, user_name: str, reset_url: str) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", "").strip()
    sender_name = os.getenv("SMTP_FROM_NAME", "CRM Sales Management").strip()
    use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}

    message = EmailMessage()
    message["Subject"] = "Reset Password – CRM Sales Management"
    message["From"] = f"{sender_name} <{sender}>"
    message["To"] = to_email
    message.set_content(
        f"Halo {user_name or 'User'},\n\n"
        "Kami menerima permintaan untuk reset password akun CRM Sales Management Anda.\n\n"
        f"Buka link berikut untuk membuat password baru:\n{reset_url}\n\n"
        "Link ini berlaku selama 30 menit dan hanya dapat digunakan satu kali.\n"
        "Jika Anda tidak meminta reset password, abaikan email ini.\n\n"
        "CRM Sales Management\n"
    )
    message.add_alternative(
        f"""<!doctype html><html><body style=\"font-family:Arial,sans-serif;color:#172033;line-height:1.6\">\n"
        f"<h2>Reset Password</h2><p>Halo {user_name or 'User'},</p>\n"
        "<p>Kami menerima permintaan untuk reset password akun CRM Sales Management Anda.</p>\n"
        f"<p><a href=\"{reset_url}\" style=\"display:inline-block;padding:12px 20px;background:#c65a24;color:#fff;text-decoration:none;border-radius:8px\">Reset Password</a></p>\n"
        "<p>Link ini berlaku selama <strong>30 menit</strong> dan hanya dapat digunakan satu kali.</p>\n"
        "<p>Jika Anda tidak meminta reset password, abaikan email ini.</p>\n"
        "</body></html>""",
        subtype="html",
    )

    with smtplib.SMTP(host, port, timeout=20) as smtp:
        if use_tls:
            smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)


async def create_reset_request(email: str) -> None:
    user = await db.users.find_one({"email": email})
    if not user:
        return

    if not smtp_configured():
        raise RuntimeError("SMTP belum dikonfigurasi")

    raw_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    await db.password_reset_tokens.delete_many({"user_id": user["id"]})
    await db.password_reset_tokens.insert_one({
        "token_hash": token_hash(raw_token),
        "user_id": user["id"],
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc),
    })

    reset_url = build_reset_url(raw_token)
    await asyncio.to_thread(send_reset_email, user.get("email", email), user.get("name", ""), reset_url)


async def reset_password(raw_token: str, new_password: str) -> bool:
    record = await db.password_reset_tokens.find_one({"token_hash": token_hash(raw_token)})
    now = datetime.now(timezone.utc)
    if not record or record.get("expires_at") <= now:
        if record:
            await db.password_reset_tokens.delete_one({"_id": record["_id"]})
        return False

    user_id = record["user_id"]
    password_hash = pwd_context.hash(new_password)
    result = await db.users.update_one({"id": user_id}, {"$set": {"password_hash": password_hash, "updated_at": now}})
    if result.modified_count != 1:
        return False

    await db.sessions.delete_many({"user_id": user_id})
    await db.password_reset_tokens.delete_one({"_id": record["_id"]})
    return True
