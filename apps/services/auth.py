"""
Module:
    auth_service.py
Deskripsi:
    Mengelola logika autentikasi utama termasuk registrasi (Sign-In),
    verifikasi OTP, login, dan manajemen token JWT melalui cookie.
Author:
    Nadhif Thoriqi
"""

import secrets
import uuid
from datetime import timedelta, datetime, timezone
from urllib.parse import quote

from environs import Env
from fastapi import BackgroundTasks, HTTPException, Response, status
from sqlmodel import select, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from ..core.security import (create_access_token, get_cookie_reset_password,
                             get_password_hash, verify_password)
from ..db.async_sessions import save_db
from ..models.auth import Auth, BlacklistToken
from ..schemas.auth import OTP, SignIn, SignUp, EditProfile
from ..schemas.auth import ChangePassword as cpassword
from ..schemas.auth import ForgotPassword as fpassword
from ..services.messages import (send_otp_email, send_reset_password,
                                 send_welcome_email)

env = Env()
env.read_env()
get_secure = env.bool("HTTPS", default=False)
get_domain = env.str("DOMAIN", default=None)
# URL frontend — sesuaikan dengan environment (dev atau production)


async def sign_up(
    data_in: SignUp, session: AsyncSession, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """
    Mendaftarkan akun baru atau mengirim ulang OTP untuk akun yang belum terverifikasi.

    Alur:
    1. Mencari user berdasarkan email.
    2. Jika user sudah ada dan terverifikasi, akses ditolak.
    3. Jika user baru atau belum verifikasi, sistem men-generate OTP 6 digit.
    4. Password di-hash dan data disimpan/diperbarui di database.
    5. OTP dikirim via email melalui BackgroundTasks.

    Args:
        data_in (SignUp): Data pendaftaran berisi name, email, dan password.
        session (AsyncSession): Sesi database async.
        background_tasks (BackgroundTasks): Untuk mengirim email OTP secara non-blocking.

    Returns:
        dict[str, str]: Pesan sukses bahwa OTP telah dikirim ke email.

    Raises:
        HTTPException: HTTP 400 jika email sudah terdaftar dan terverifikasi.
    """

    # 1. Cari user berdasarkan email
    result = await session.exec(select(Auth).where(Auth.email == data_in.email))
    existing_user = result.first()

    # 2. Logika Pengecekan
    if existing_user:
        if existing_user.is_verified:
            # Jika sudah verifikasi, baru kita larang (Email benar-benar terpakai)
            raise HTTPException(status_code=400, detail="Email sudah terdaftar")

        existing_user.hashed_password = get_password_hash(data_in.password)
        otp_code = secrets.randbelow(900000) + 100000
        existing_user.otp_code = otp_code

        db_user = existing_user

    else:
        # Jika benar-external baru, buat object baru
        otp_code = secrets.randbelow(900000) + 100000
        db_user = Auth(
            name=data_in.name,
            email=data_in.email,
            hashed_password=get_password_hash(data_in.password),
            otp_code=otp_code,
            is_verified=False,
        )

    # 3. Eksekusi Perubahan
    await save_db(session, db_user)

    base_domain = get_domain if get_domain is not None else "http://localhost:5500"
    # 4. Buat link langsung ke halaman Verify (email sudah di-encode agar aman di URL)
    verify_url = f"{base_domain}?email={quote(db_user.email)}&page=verify"

    # 5. Kirim OTP via email beserta link halaman Verify
    background_tasks.add_task(
        send_otp_email, db_user.email, db_user.name, f"{otp_code}", verify_url
    )

    return {
        "status": "success",
        "message": "Kode verifikasi baru telah dikirim ke email Anda.",
    }

async def resend_otp(
    data_in: OTP, session: AsyncSession, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """
    Mengirim ulang kode OTP ke email pengguna yang belum terverifikasi.

    Alur:
    1. Mencari user berdasarkan email.
    2. Memvalidasi bahwa user ada dan belum terverifikasi.
    3. Men-generate OTP baru dan memperbaruinya di database.
    4. Mengirim OTP baru via email beserta link halaman verifikasi.

    Args:
        data_in (OTP): Data berisi email pengguna.
        session (AsyncSession): Sesi database async.
        background_tasks (BackgroundTasks): Untuk mengirim email OTP secara non-blocking.

    Returns:
        dict[str, str]: Pesan sukses bahwa OTP baru telah dikirim ke email.

    Raises:
        HTTPException: HTTP 400 jika email tidak ditemukan atau sudah terverifikasi.
    """
    # 1. Cari user berdasarkan email
    result = await session.exec(select(Auth).where(Auth.email == data_in.email))
    db_user = result.first()

    # 2. Logika Pengecekan
    if db_user is None:
        raise HTTPException(status_code=400, detail="Alamat Email tidak terdeteksi")

    if db_user.is_verified:
        # Jika sudah verifikasi, baru kita larang (Email benar-benar terpakai)
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    otp_code = secrets.randbelow(900000) + 100000
    db_user.otp_code = otp_code

    # 3. Eksekusi Perubahan
    await save_db(session, db_user)

    # 4. Buat link langsung ke halaman Verify (email sudah di-encode agar aman di URL)
    base_domain = get_domain if get_domain else "http://localhost:5500"
    verify_url = f"{base_domain}?email={quote(db_user.email)}&page=verify"

    # 5. Kirim OTP via email beserta link halaman Verify
    background_tasks.add_task(
        send_otp_email, db_user.email, db_user.name, f"{otp_code}", verify_url
    )

    return {
        "status": "success",
        "message": "Kode verifikasi baru telah dikirim ke email Anda.",
    }

async def token(
    user_id: uuid.UUID, response: Response, session: AsyncSession
) -> dict[str, str]:
    """
    Menghasilkan JWT dan menyimpannya ke dalam HTTPOnly Cookie.

    Security:
    - httponly=True: Mencegah akses token oleh JavaScript (Proteksi XSS).
    - samesite="lax": Proteksi dasar terhadap serangan CSRF.
    - max_age: Berlaku selama 3 hari (259.200 detik).

    Args:
        user_id (uuid.UUID): ID pengguna yang akan dimasukkan ke payload token.
        response (Response): Objek response FastAPI untuk menyimpan cookie.
        session (AsyncSession): Sesi database async untuk mengambil data pengguna.

    Returns:
        dict[str, str]: Pesan konfirmasi bahwa login berhasil.

    Raises:
        HTTPException: HTTP 401 jika user tidak ditemukan di database.
    """
    user = await session.get(Auth, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User tidak ditemukan di database.")

    token_data = {
        "sub": str(user_id),  # Tetap gunakan ID sebagai acuan utama
        "email": user.email,  # Sertakan email untuk kebutuhan instan di frontend
        "name": user.name,  # Sertakan name untuk kebutuhan instan di frontend
        "type": "access",  # Penanda bahwa ini token login biasa, BUKAN token reset password
    }
    access_token = str(
        create_access_token(data=token_data, expires_delta=timedelta(days=30))
    )

    # Simpan token ke Cookie (HTTPOnly untuk keamanan)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # JavaScript tidak bisa mengakses cookie
        max_age=2592000,  # 30 hari
        expires=2592000,
        samesite="lax",  # Proteksi dasar CSRF
        secure=get_secure,  # Ubah ke True jika sudah HTTPS
        domain=get_domain,  # biarkan None, jangan diisi manual
        path="/",  # ← wajib "/" agar berlaku di semua halaman
    )

    return {"status": "success", "message": "Login berhasil"}

async def verify_account(
    response: Response,
    email: str,
    otp: int,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """
    Memvalidasi kode OTP yang dimasukkan pengguna.  
    Jika sukses, status akun menjadi aktif (is_verified=True)
        dan pengguna langsung mendapatkan token login.

    Args:
        response (Response): Objek response FastAPI untuk menyimpan cookie token setelah verifikasi.
        email (str): Email pengguna yang melakukan verifikasi.
        otp (int): Kode OTP 6 digit yang dimasukkan pengguna.
        session (AsyncSession): Sesi database async.
        background_tasks (BackgroundTasks): Untuk mengirim email selamat datang
            secara non-blocking.

    Returns:
        dict[str, str]: Pesan sukses login setelah verifikasi berhasil, 
            atau pesan error jika akun sudah aktif.

    Raises:
        HTTPException: HTTP 404 jika user tidak ditemukan, HTTP 400 jika kode OTP salah.
    """
    result = await session.exec(select(Auth).where(Auth.email == email))
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if user.is_verified:
        return {"status": "error", "message": "Akun sudah aktif, silakan login"}

    if user.otp_code != otp:
        raise HTTPException(status_code=400, detail="Kode OTP salah")

    # Verifikasi sukses
    user.is_verified = True
    user.otp_code = None  # Bersihkan kode OTP
    await save_db(session, user)

    background_tasks.add_task(send_welcome_email, user.email, user.name)
    return await token(user.id, response, session)

async def sign_in(
    response: Response, request: SignIn, session: AsyncSession
) -> dict[str, str]:
    """
    Melakukan autentikasi pengguna menggunakan form OAuth2.

    Validasi:
    1. Cek keberadaan email.
    2. Verifikasi kecocokan password hash.
    3. Pastikan akun sudah melalui proses verifikasi email (OTP).

    Args:
        response (Response): Objek response FastAPI untuk menyimpan cookie token.
        request (SignIn): Data login berisi email dan password.
        session (AsyncSession): Sesi database async.

    Returns:
        dict[str, str]: Pesan sukses login beserta token dalam cookie.

    Raises:
        HTTPException: HTTP 401 jika email/password salah, HTTP 403 jika akun belum terverifikasi.
    """
    # Cari user berdasarkan email
    result = await session.exec(select(Auth).where(Auth.email == request.email))
    user_found = result.first()

    # Validasi user dan password
    if not user_found or not verify_password(
        request.password, user_found.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password anda salah",
        )

    # TAMBAHAN: Cek apakah user sudah verifikasi email
    if not user_found.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun Anda belum dikonfirmasi. Silakan verifikasi email Anda.",
        )

    return await token(user_found.id, response, session)

async def forgot_password(
    forgot: fpassword, session: AsyncSession, background_tasks: BackgroundTasks
) -> None:
    """
    Memproses permintaan lupa password dengan mengirim link reset ke email pengguna.

    Membuat JWT token bertipe 'reset_password' yang berlaku 1 jam,
    lalu mengirimkan link reset password yang mengandung token tersebut ke email pengguna.

    Args:
        forgot (ForgotPassword): Data berisi email pengguna.
        session (AsyncSession): Sesi database async.
        background_tasks (BackgroundTasks): Untuk mengirim email reset password secara non-blocking.

    Returns:
        None

    Raises:
        HTTPException: HTTP 401 jika user tidak ditemukan di database.
    """
    result = await session.exec(select(Auth).where(Auth.email == forgot.email))
    user = result.first()

    if user is None:
        raise HTTPException(status_code=401, detail="User tidak ditemukan di database.")

    token_data = {
        # Menggunakan ID user sebagai sub primer
        "sub": str(user.id),  
        # Mengambil email dinamis dari database pengguna
        "email": forgot.email,  
        # Rekomendasi tambahan: tandai tipe token agar tidak disalahgunakan untuk login biasa
        "type": "reset_password",  
    }
    access_token = create_access_token(
        data=token_data, expires_delta=timedelta(hours=1)
    )
    base_domain = get_domain if get_domain is not None else "http://localhost:5500"
    verify_url = f"{base_domain}?token={quote(access_token)}&page=reset"
    background_tasks.add_task(
        send_reset_password,
        to=forgot.email,
        username=forgot.email,
        reset_url=verify_url,
    )

async def edit_auth(
    edit_in: cpassword | EditProfile, 
    session: AsyncSession, 
    token: Auth | None = None
) -> SQLModel:
    """
    Mengubah password pengguna menggunakan token reset yang valid.

    Memvalidasi token reset password, lalu mengganti password lama
    dengan hash dari password baru yang diberikan.

    Args:
        edit_in (ChangePassword): Data berisi token reset dan password baru.
        session (AsyncSession): Sesi database async.

    Returns:
        None (hasil save_db dikembalikan namun tidak digunakan oleh pemanggil).
    """
    if isinstance(edit_in, cpassword):
        cookie = await get_cookie_reset_password(session, edit_in.token)
        auth = await session.get(Auth, cookie)
    
        if auth is None:
            raise HTTPException(status_code=401, detail="Payload token tidak valid")
            
        auth.hashed_password = get_password_hash(edit_in.password)

    else:
        if token is None:
            raise HTTPException(status_code=401, detail="Token diperlukan untuk mengubah profil")
            
        auth = await session.get(Auth, token)
        
        if auth is None:
            raise HTTPException(status_code=401, detail="Payload token tidak valid")
            
        # Update fields secara dinamis jika dikirimkan
        if edit_in.email is not None:
            auth.email = edit_in.email
        if edit_in.name is not None:
            auth.name = edit_in.name

    # Memastikan data hanya disimpan jika objek auth berhasil ditemukan/dimodifikasi
    return await save_db(session, auth)

async def logout_account(
    response: Response, get_token: str, session: AsyncSession
) -> dict[str, str]:
    """
    Mengakhiri session pengguna.

    Proses:
    1. Memasukkan token aktif ke tabel BlacklistToken agar tidak bisa digunakan kembali.
    2. Menghapus cookie 'access_token' dari browser pengguna.

    Args:
        response (Response): Objek response FastAPI untuk menghapus cookie.
        request (Request): Objek request FastAPI untuk membaca token dari cookie.
        session (AsyncSession): Sesi database async untuk menyimpan token ke blacklist.

    Returns:
        dict[str, str]: Pesan konfirmasi bahwa logout berhasil.

    Raises:
        HTTPException: HTTP 404 jika token tidak ditemukan di cookie (user belum login).
    """
    if not get_token:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    # Tambahkan token ke blacklist
    new_blacklist = BlacklistToken(token=get_token)
    await save_db(session, new_blacklist)

    # Hapus cookie
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        # Pastikan path sama dengan set_cookie jika pernah diatur
    )

    return {"status": "success", "message": "Berhasil logout"}

async def delete_account(
    user: Auth,
    session: AsyncSession
):
    current_time = datetime.now(timezone.utc)
        
    # 1. Ubah email agar constraint UNIQUE lepas
    user.email = f"{user.email}//deleted//{int(current_time.timestamp())}"
    user.deleted_at = current_time
    
    await save_db(session, user)
    return {"message": "Akun berhasil dihapus"}