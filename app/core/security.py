from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.auth_model import BlacklistToken

import jwt  # Ini adalah PyJWT
import bcrypt
import os

# Muat file .env
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "KUNCI_SANGAT_RAHASIA")
ALGORITHM = "HS256"

print(SECRET_KEY)

def get_password_hash(password: str) -> str:
    """
    Menghasilkan hash password dengan salt.

    Format penyimpanan:
    salt$hash
    """
        
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifikasi password saat login.
    """
    
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Membuat JWT access token.

    Data minimal biasanya:
    {
        "sub": user_id
    }
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
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_token(request: Request) -> str:
    """
    Mendukung 2 metode autentikasi:

    1. Cookie (Untuk Web Browser)
    2. Authorization Header Bearer (Untuk Mobile/Postman)
    """

    # 1️⃣ Cek Cookie
    token_cookie = request.cookies.get("access_token")
    if token_cookie:
        return token_cookie

    # 2️⃣ Cek Authorization Header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    # Jika token tidak ditemukan
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesi login tidak ditemukan. Silakan login terlebih dahulu."
    )

# tokenUrl merijik pada url login/pembuatan token anda
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(
        # GUNAKAN get_token agar fitur Cookie & Header bekerja dua-duanya
        token: str = Depends(get_token), 
        session: Session = Depends(get_session)
    ):
    
    # 1. Cek Blacklist
    is_blacklisted = session.exec(
        select(BlacklistToken).where(BlacklistToken.token == token)
    ).first()

    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sudah tidak berlaku (sudah logout)"
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(status_code=401, detail="Payload token tidak valid")
        return username
    
    # URUTAN PENTING: Dari yang spesifik ke yang umum
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sudah kadaluwarsa, silakan login ulang"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token rusak atau tidak valid"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gagal memproses token"
        )