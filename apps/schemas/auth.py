"""
Module:
    schemas/auth.py
Deskripsi:
    Mendefinisikan skema Pydantic (DTO - Data Transfer Object) untuk
    validasi dan serialisasi data request/response pada fitur autentikasi.
    Skema ini digunakan sebagai kontrak data antara client dan API.
"""

import uuid

from pydantic import BaseModel, EmailStr


class OTP(BaseModel):
    """
    Skema dasar yang hanya berisi email. Digunakan sebagai base class
    dan secara langsung untuk endpoint resend-otp dan forgot-password.

    Attributes:
        email (EmailStr): Alamat email yang divalidasi format-nya oleh Pydantic.
    """

    email: EmailStr


class SignIn(OTP):
    """
    Skema untuk request login pengguna.

    Attributes:
        email (EmailStr): Alamat email pengguna (diwarisi dari OTP).
        password (str): Password plaintext pengguna.
    """

    password: str


class SignUp(SignIn):
    """
    Skema untuk request pendaftaran akun baru.

    Attributes:
        email (EmailStr): Alamat email pengguna (diwarisi dari OTP).
        password (str): Password plaintext pengguna (diwarisi dari SignIn).
        name (str): Nama lengkap pengguna.
    """

    name: str


class ForgotPassword(OTP):
    """
    Skema untuk request lupa password. Hanya membutuhkan email.
    Menggunakan OTP secara langsung tanpa menambah field baru.
    """


class VerifyOTP(OTP):
    """
    Skema untuk request verifikasi OTP saat aktivasi akun.

    Attributes:
        email (EmailStr): Alamat email pengguna (diwarisi dari OTP).
        otp (int): Kode OTP 6 digit yang dikirim ke email pengguna.
    """

    otp: int


class ChangePassword(BaseModel):
    """
    Skema untuk request reset/ubah password menggunakan token.

    Attributes:
        token (str): JWT token bertipe 'reset_password' yang dikirim via email.
        password (str): Password baru yang diinginkan pengguna.
    """

    token: str
    password: str


class EditProfile(BaseModel):
    email: EmailStr|None = None
    name: str|None = None


class ShowMe(BaseModel):
    """
    Skema response untuk menampilkan data profil pengguna yang sedang login.
    Digunakan pada endpoint GET /auth/me.

    Attributes:
        id (uuid.UUID): ID unik pengguna.
        name (str | EmailStr): Nama pengguna.
        email (str): Alamat email pengguna.
        is_verified (bool): Status verifikasi akun.
        role (str): Peran pengguna dalam sistem (admin/buyer).
    """

    id: uuid.UUID
    name: str | EmailStr
    email: str
    is_verified: bool
    role: str
