"""
Module:
    mail_service.py
Deskripsi:
    Layanan pengiriman email berbasis FastAPI-Mail untuk menangani berbagai
    kebutuhan seperti OTP, email sambutan, broadcast, dan lampiran.
Author:
    Nadhif Thoriqi
Dependencies:
    fastapi-mail, pydantic, fastapi
"""

from pathlib import Path
from typing import Any, Dict, List, Union, cast

from environs import Env
from fastapi import UploadFile
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr, NameEmail, SecretStr

env = Env()
env.read_env()
# ── Konfigurasi Direktori ───────────────────────────────────────────────────
# Membuat folder templates otomatis jika belum ada untuk menyimpan file .html
TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_DIR.mkdir(exist_ok=True)

# ── Konfigurasi SMTP ──────────────────────────────────────────────────────────
# Pengaturan koneksi ke server Gmail SMTP
conf = ConnectionConfig(
    MAIL_USERNAME=env.str("MAIL_USERNAME"),
    MAIL_PASSWORD=SecretStr(env.str("MAIL_PASSWORD")),
    MAIL_FROM=env.str("MAIL_FROM"),
    MAIL_FROM_NAME="Email Bot",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=TEMPLATE_DIR,
)

fm = FastMail(conf)

# ── Fungsi Kirim Email ────────────────────────────────────────────────────────


async def send_email(to: List[EmailStr], subject: str, body: str) -> None:
    """
    Kirim email HTML umum menggunakan template general.html.

    Args:
        to: Daftar alamat email penerima.
        subject: Judul email.
        body: Isi pesan dalam format teks/HTML.
    """
    recipients: List[NameEmail] = cast(List[NameEmail], to)
    msg = MessageSchema(
        recipients=recipients,
        subject=subject,
        template_body={"subject": subject, "body": body},
        subtype=MessageType.html,
    )
    await fm.send_message(msg, template_name="general.html")


async def send_welcome_email(
    to: EmailStr, username: str, verification_url: str | None = None
) -> None:
    """
    Kirim email selamat datang ke pengguna baru (template welcome.html).

    Args:
        to (EmailStr): Alamat email pengguna baru.
        username (str): Nama pengguna yang akan ditampilkan di email.
        verification_url (str | None): URL verifikasi opsional untuk disertakan di email.
    """
    recipients: NameEmail = cast(NameEmail, to)
    msg = MessageSchema(
        recipients=[recipients],
        subject=f"Selamat Datang, {username}!",
        template_body={
            "username": username,
            "verification_url": verification_url,
        },
        subtype=MessageType.html,
    )
    await fm.send_message(msg, template_name="welcome.html")


async def send_otp_email(
    to: EmailStr,
    username: str,
    otp: str,
    verify_url: str | None = None,
    expiry_minutes: int = 5,
) -> str:
    """
    Kirim kode OTP verifikasi ke email (template otp.html).

    Args:
        to (EmailStr): Alamat email penerima.
        username (str): Nama pengguna yang akan ditampilkan di email.
        otp (str): Kode OTP 6 digit yang akan dikirimkan.
        verify_url: Link langsung ke halaman Verify (opsional). Jika diberikan,
                    email akan menyertakan tombol/link untuk membuka halaman verify
                    secara langsung — berguna jika pengguna tidak sengaja menutup tab.
        expiry_minutes (int): Durasi berlakunya OTP dalam menit (default: 5 menit).

    Returns:
        str: Mengembalikan kode OTP yang dikirim untuk disimpan di database.
    """
    recipients: NameEmail = cast(NameEmail, to)
    msg = MessageSchema(
        recipients=[recipients],
        subject="Kode OTP Verifikasi",
        template_body={
            "username": username,
            "otp_code": otp,
            "expiry_minutes": expiry_minutes,
            "verify_url": verify_url,
        },
        subtype=MessageType.html,
    )
    await fm.send_message(msg, template_name="otp.html")
    return otp


async def send_bulk_email(
    recipients: List[Dict[str, Any]], subject: str, body: str
) -> Dict[str, Any]:
    """
    Kirim email ke banyak penerima secara sekaligus.

    Args:
        recipients: List dictionary berisi 'email' dan 'name'.
        subject (str): Judul email yang akan dikirim ke semua penerima.
        body (str): Isi pesan dalam format teks/HTML.

    Returns:
        Dict: Laporan berisi daftar email yang sukses dan gagal dikirim.
    """
    success: List[Any] = []
    failed: List[Any] = []
    for r in recipients:
        try:
            msg = MessageSchema(
                recipients=[r["email"]],
                subject=subject,
                template_body={
                    "subject": subject,
                    "username": r.get("name", "Pengguna"),
                    "body": body,
                },
                subtype=MessageType.html,
            )
            await fm.send_message(msg, template_name="general.html")
            success.append(r["email"])
        except ConnectionErrors as e:
            failed.append({"email": r["email"], "error": str(e)})
    return {"success": success, "failed": failed}


async def send_reset_password(to: EmailStr, username: str, reset_url: str):
    """
    Kirim email reset password berisi link untuk mengubah password (template reset_password.html).

    Args:
        to (EmailStr): Alamat email penerima.
        username (str): Nama atau email pengguna yang akan ditampilkan di email.
        reset_url (str): URL reset password yang mengandung token JWT bertipe 'reset_password'.
    """
    recipients: NameEmail = cast(NameEmail, to)
    msg = MessageSchema(
        recipients=[recipients],
        subject="Reset Password",
        template_body={"username": username, "reset_url": reset_url},
        subtype=MessageType.html,
    )
    await fm.send_message(msg, template_name="reset_password.html")


async def send_email_with_attachment(
    to: List[NameEmail],
    subject: str,
    body: str,
    attachment_paths: List[Union[UploadFile, Dict[str, Any], str]],
) -> None:
    """
    Kirim email dengan lampiran file.

    Args:
        to (List[NameEmail]): Daftar alamat email penerima.
        subject (str): Judul email.
        body (str): Isi pesan dalam format teks/HTML.
        attachment_paths: List berisi path file (str), UploadFile, atau Dict lampiran.
    """
    # Gunakan cast untuk menghindari error 'Invariance' pada list
    validated_attachments = cast(List[Any], attachment_paths)

    msg = MessageSchema(
        recipients=to,
        subject=subject,
        body=body,
        subtype=MessageType.html,
        attachments=validated_attachments,
    )
    await fm.send_message(msg)
