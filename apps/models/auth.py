"""
Module:
    models/auth.py
Deskripsi:
    Mendefinisikan model database (tabel) untuk fitur autentikasi
    menggunakan SQLModel sebagai ORM.

Tables:
    auth            - Menyimpan data pengguna terdaftar.
    blacklist_token - Menyimpan token JWT yang sudah tidak berlaku (logout).
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import EmailStr
from sqlalchemy import TIMESTAMP
from sqlmodel import Column, Field, SQLModel

from ..core.enums import Role


class Auth(SQLModel, table=True):
    """
    Model tabel 'auth' yang menyimpan data akun pengguna.

    Attributes:
        id (uuid.UUID): Primary key unik yang di-generate otomatis.
        name (str): Nama lengkap pengguna.
        email (EmailStr): Alamat email unik pengguna, divalidasi oleh Pydantic.
        hashed_password (str): Password yang sudah di-hash menggunakan bcrypt.
        is_verified (bool): Status verifikasi akun (True jika sudah verifikasi OTP).
        otp_code (int | None): Kode OTP 6 digit untuk verifikasi. None jika sudah terverifikasi.
        role (Role): Peran pengguna dalam sistem (default: BUYER).
    """

    __tablename__: Any = "auth"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True, unique=True
    )
    name: str
    email: EmailStr = Field(max_length=255, index=True, unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    is_verified: bool = Field(default=False)
    otp_code: int | None = Field(default=None, nullable=True)
    role: Role = Field(default=Role.BUYER, nullable=False)


class BlacklistToken(SQLModel, table=True):
    """
    Model tabel 'blacklist_token' yang menyimpan token JWT yang sudah di-logout.

    Token yang ada di tabel ini dianggap tidak berlaku dan tidak bisa digunakan
    untuk autentikasi meskipun secara teknis belum kadaluwarsa.

    Attributes:
        id (uuid.UUID): Primary key unik yang di-generate otomatis.
        token (str): String JWT token yang di-blacklist.
        blacklisted_at (datetime): Timestamp saat token dimasukkan ke daftar hitam (timezone-aware).
    """

    __tablename__: Any = "blacklist_token"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,  # Gunakan default_factory untuk fungsi
        primary_key=True,
        index=True,
        unique=True,
    )
    token: str = Field(index=True, unique=True, nullable=False)
    blacklisted_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
