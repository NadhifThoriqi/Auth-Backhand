from fastapi import Response, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.auth_model import Auth, BlacklistToken
from app.schemas.auth_schema import SignInAuth

def sign_in(dataIn: SignInAuth, session: Session): 
    """
    Membuat akun baru.

    Alur:
    1. Cek apakah email sudah terdaftar
    2. Hash password menggunakan PBKDF2
    3. Simpan user ke database
    """

    # Cek apakah email sudah ada
    if session.exec(select(Auth).where(Auth.email == dataIn.email)).first():
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    
    # Hash password sebelum disimpan
    hashed = get_password_hash(dataIn.password)
    
    # Buat object user baru
    db_user = Auth(
        username="Guest",   # Default username
        email=dataIn.email,
        hashed_password=hashed
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user

def log_in(response: Response, request: OAuth2PasswordRequestForm, session: Session):
    """
    Login user.

    Alur:
    1. Cari user berdasarkan email
    2. Verifikasi password
    3. Buat JWT token
    4. Simpan token ke cookie
    """

    # Cari user berdasarkan email
    statement = select(Auth).where(Auth.email == request.username)
    user_found = session.exec(statement).first()

    # Validasi user dan password
    if not user_found or not verify_password(
        request.password,
        user_found.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password anda salah"
        )

    # Buat token JWT (sub = user_id)
    token_data = {"sub": str(user_found.id)}
    access_token = create_access_token(data=token_data)
    
    # Simpan token ke Cookie (HTTPOnly untuk keamanan)
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True,      # JavaScript tidak bisa mengakses cookie
        max_age=259200,     # 3 hari
        expires=259200,
        samesite="lax",     # Proteksi dasar CSRF
        secure=False,       # Ubah ke True jika sudah HTTPS
    )

    return {  "status": "success", "message": "Login berhasil"}

def logout_account(response: Response, token: str, session: Session):
    """
    Logout user.

    Alur:
    1. Masukkan token ke blacklist database
        → agar token tidak bisa dipakai lagi
    2. Hapus cookie di browser
    """

    # Tambahkan token ke blacklist
    new_blacklist = BlacklistToken(token=token)
    session.add(new_blacklist)
    session.commit()

    # Hapus cookie
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        # Pastikan path sama dengan set_cookie jika pernah diatur
    )
    
    return {"message": "Berhasil logout"}