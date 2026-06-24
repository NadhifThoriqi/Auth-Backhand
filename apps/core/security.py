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
from environs import Env
from fastapi import HTTPException, status, Cookie, Header, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models.auth import Auth, BlacklistToken
from ..db.async_sessions import get_session_async

env = Env()
env.read_env()
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


async def _get_cookie(
    session: AsyncSession, 
    access_token: str | None = Cookie(None), 
    authorization: str | None = Header(None)
) -> Dict[str, str]:
     # 1. Prioritaskan cek Cookie terlebih dahulu
    if access_token:
        token = access_token

    # 2. Jika tidak ada di cookie, cek Authorization Header (Bearer Token)
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    else:
        raise HTTPException(status_code=401, detail="Log in dulu yuk")

    is_blacklisted = await session.get(BlacklistToken, token)

    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sudah tidak berlaku (sudah logout)",
        )
    try:
        # Decode kembali tokennya
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token sudah kadaluwarsa, silakan login ulang")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token rusak atau tidak valid")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Gagal memproses token")

    return payload


def get_current_user(return_user_object: bool | None = True):
    async def dependency(
        session: AsyncSession = Depends(get_session_async), 
        access_token: str | None = Cookie(None), 
        authorization: str | None = Header(None),
    ) -> Auth | str:
        payload = await _get_cookie(session, access_token, authorization)
        token_type = payload.get("type")
        # Pastikan tipe token adalah untuk login/access, bukan reset_password
        if token_type != "access":  # nosec
            raise HTTPException(
                status_code=401, detail="Tipe token tidak valid untuk login"
            )
        
        token_id = payload.get("sub")
        if token_id is None:
            raise HTTPException(status_code=401, detail="Token tidak valid")

        if return_user_object:
            user = await session.get(Auth, token_id)
            if user is None:
                raise HTTPException(status_code=401, detail="User tidak ditemukan")
            return user  # Mengembalikan objek Auth

        return token_id
    
    return dependency

async def get_cookie_reset_password(
    session: AsyncSession,
    access_token: str | None = Cookie(None)
) -> Auth:
    payload = await _get_cookie(session, access_token)
    token_type = payload.get("type")
    # Pastikan tipe token adalah untuk login/access, bukan reset_password
    if token_type != "reset_password":  # nosec
        raise HTTPException(
            status_code=401, detail="Tipe token tidak valid untuk ganti password"
        )

    token_id = payload.get("sub")
    user = await session.get(Auth, token_id)

    if user is None:
        raise HTTPException(status_code=401, detail="User tidak ditemukan atau token tidak valid")
    return user