import asyncio
import os
import smtplib
from email.message import EmailMessage


def _smtp_configured() -> bool:
    return all(
        os.getenv(key, "").strip()
        for key in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM")
    )


def _send_message(message: EmailMessage) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587").strip() or "587")
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}

    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(message)


async def send_password_reset_email(to_email: str, user_name: str, reset_url: str) -> None:
    if not _smtp_configured():
        raise RuntimeError("SMTP email belum dikonfigurasi pada environment aplikasi")

    sender_name = os.getenv("SMTP_FROM_NAME", "CRM Sales Management").strip() or "CRM Sales Management"
    message = EmailMessage()
    message["Subject"] = "Reset Password – CRM Sales Management"
    message["From"] = f"{sender_name} <{os.getenv('SMTP_FROM').strip()}>"
    message["To"] = to_email
    message.set_content(
        f"""Halo {user_name},

Kami menerima permintaan untuk mereset password akun CRM Sales Management Anda.

Gunakan link berikut untuk membuat password baru:
{reset_url}

Link ini hanya berlaku selama 30 menit dan hanya dapat digunakan satu kali.

Jika Anda tidak meminta reset password, abaikan email ini.

Salam,
{sender_name}
"""
    )
    message.add_alternative(
        f"""<!doctype html>
<html>
  <body style="font-family:Arial,sans-serif;color:#172033;line-height:1.6">
    <div style="max-width:600px;margin:auto;padding:32px;border:1px solid #e5e7eb;border-radius:16px">
      <h2 style="margin-top:0">Reset Password</h2>
      <p>Halo <strong>{user_name}</strong>,</p>
      <p>Kami menerima permintaan untuk mereset password akun CRM Sales Management Anda.</p>
      <p>
        <a href="{reset_url}" style="display:inline-block;padding:12px 20px;background:#ea580c;color:#fff;text-decoration:none;border-radius:8px;font-weight:600">Reset Password</a>
      </p>
      <p style="font-size:13px;color:#64748b">Link berlaku selama 30 menit dan hanya dapat digunakan satu kali.</p>
      <p style="font-size:13px;color:#64748b">Jika Anda tidak meminta reset password, abaikan email ini.</p>
    </div>
  </body>
</html>""",
        subtype="html",
    )

    await asyncio.to_thread(_send_message, message)
