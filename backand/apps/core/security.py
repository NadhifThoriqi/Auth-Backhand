"""
Module:
    core/security.py
Deskripsi:
    Menyediakan utilitas keamanan inti aplikasi, meliputi:
    - Hashing dan verifikasi password menggunakan bcrypt.
    - Pembuatan dan dekoding JWT access token.
    - Ekstraksi token dari request (cookie atau Authorization header).
    - Validasi pengguna aktif dari token JWT.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import bcrypt
import jwt
from dotenv import load_dotenv
from environs import Env
from fastapi import HTTPException, Request, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models.auth import Auth, BlacklistToken

# Muat file .env
load_dotenv()

env = Env()
SECRET_KEY = env.str("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY tidak ditemukan di environment variables!")

ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    """
    Menghasilkan hash password dengan salt.

    Format penyimpanan:
    salt$hash

    Args:
        password (str): Password plaintext yang akan di-hash.

    Returns:
        str: String hash password yang aman untuk disimpan di database.
    """

    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifikasi password saat login.

    Args:
        plain_password (str): Password plaintext yang dimasukkan pengguna.
        hashed_password (str): Hash password yang tersimpan di database.

    Returns:
        bool: True jika password cocok, False jika tidak cocok.
    """

    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(
    data: Dict[str, Any], expires_delta: timedelta | None = None
) -> bytes:
    """
    Membuat JWT access token.

    Data minimal biasanya:
    {
        "sub": user_id
    }

    Args:
        data (Dict[str, Any]): Payload data yang akan dikodekan ke dalam token.
        expires_delta (timedelta | None): Durasi token berlaku. Default 7 hari jika None.

    Returns:
        bytes: JWT token yang telah dikodekan sebagai string.
    """
    to_encode = data.copy()

    # Gunakan timezone-aware datetime agar lebih akurat dan aman
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)

    # Payload JWT
    to_encode.update({"exp": expire})

    # Encode menggunakan PyJWT
    encoded_jwt = jwt.encode(payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_token(request: Request) -> str:
    """
    Mendukung 2 metode autentikasi:

    1. Cookie (Untuk Web Browser)
    2. Authorization Header Bearer (Untuk Mobile/Postman)

    Args:
        request (Request): Objek HTTP request dari FastAPI.

    Returns:
        str: Token JWT yang ditemukan dari cookie atau Authorization header.

    Raises:
        HTTPException: HTTP 401 jika token tidak ditemukan di kedua sumber.
    """

    # Cek Cookie
    token_cookie = request.cookies.get("access_token")
    if token_cookie:
        return token_cookie

    # Cek Authorization Header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    # Jika token tidak ditemukan
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesi login tidak ditemukan. Silakan login terlebih dahulu.",
    )


async def get_current_user(token: str, session: AsyncSession) -> Auth:
    """
    Memvalidasi token JWT dan mengembalikan objek pengguna yang sedang aktif.

    Proses validasi:
    1. Memeriksa apakah token ada di daftar hitam (blacklist/sudah logout).
    2. Mendekode token JWT dan memvalidasi signature serta masa berlakunya.
    3. Mengambil data pengguna dari database berdasarkan ID di payload token.
    4. Memastikan tipe token adalah 'access' atau 'reset_password'.

    Args:
        token (str): JWT token yang akan divalidasi.
        session (AsyncSession): Sesi database async untuk query data pengguna.

    Returns:
        Auth: Objek model pengguna yang ditemukan di database.

    Raises:
        HTTPException: HTTP 401 jika token di-blacklist, kadaluwarsa, tidak valid,
                       payload tidak lengkap, tipe token salah, atau user tidak ditemukan.
    """
    # 1. Cek Blacklist
    statement = select(BlacklistToken).where(BlacklistToken.token == token)
    result = await session.exec(statement)
    is_blacklisted = result.first()

    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sudah tidak berlaku (sudah logout)",
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=401, detail="Token sudah kadaluwarsa, silakan login ulang"
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=401, detail="Token rusak atau tidak valid"
        ) from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Gagal memproses token") from exc

    # Logika setelah decode — di luar try/except JWT
    token_id = payload.get("sub")
    if not token_id:
        raise HTTPException(status_code=401, detail="Payload token tidak valid")

    token_type = payload.get("type")
    # Pastikan tipe token adalah untuk login/access, bukan reset_password
    if token_type not in ["access", "reset_password"]:  # nosec
        raise HTTPException(
            status_code=401, detail="Tipe token tidak valid untuk login"
        )

    user = await session.get(Auth, token_id)
    print(token_id, user)
    if user is None:
        raise HTTPException(status_code=401, detail="User tidak ditemukan di database")

    return user
