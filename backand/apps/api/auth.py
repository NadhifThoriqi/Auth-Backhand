"""
Module:
    api/auth.py
Deskripsi:
    Mendefinisikan semua endpoint HTTP untuk fitur autentikasi pengguna.
    Bertindak sebagai lapisan routing yang meneruskan request ke fungsi
    service yang sesuai di apps/services/auth.py.

Endpoints:
    GET  /auth/me             - Mengambil data pengguna yang sedang login.
    POST /auth/sign-up        - Mendaftarkan akun baru dan mengirim OTP ke email.
    POST /auth/resend-otp     - Mengirim ulang kode OTP ke email pengguna.
    POST /auth/verify         - Memverifikasi kode OTP untuk mengaktifkan akun.
    POST /auth/sign-in        - Login dengan email dan password.
    POST /auth/forgot         - Mengirim link reset password ke email.
    DELETE /auth/log-out      - Logout dan menghapus session pengguna.
    PATCH /auth/reset-password - Mengubah password menggunakan token reset.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from sqlmodel.ext.asyncio.session import AsyncSession

from ..core.security import get_current_user, get_token
from ..db.async_sessions import get_session_async
from ..models.auth import Auth
from ..schemas.auth import (OTP, ChangePassword, ForgotPassword, ShowMe,
                            SignIn, SignUp, VerifyOTP)
from ..services.auth import edit_auth as ea
from ..services.auth import forgot_password as fp
from ..services.auth import logout_account as la
from ..services.auth import resend_otp as ro
from ..services.auth import sign_in as si
from ..services.auth import sign_up as up
from ..services.auth import verify_account as va

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me", response_model=ShowMe)
async def read_users_me(
    token: str = Depends(get_token), session: AsyncSession = Depends(get_session_async)
) -> Auth:
    """
    Mengambil data profil pengguna yang sedang aktif/login.

    Args:
        token (str): JWT access token dari cookie atau Authorization header.
        session (AsyncSession): Sesi database async yang di-inject oleh FastAPI.

    Returns:
        Auth: Objek data pengguna yang sesuai dengan skema ShowMe.
    """
    user = await get_current_user(token, session)
    return user


@router.post("/sign-up")
async def sign_up(
    data_in: SignUp,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session_async),
) -> dict[str, str]:
    """
    Mendaftarkan akun baru atau mengirim ulang OTP untuk akun yang belum terverifikasi.

    Jika email sudah terdaftar dan sudah terverifikasi, request akan ditolak.
    Jika email sudah ada tapi belum terverifikasi, OTP baru akan dikirim ulang.

    Args:
        data_in (SignUp): Data pendaftaran (name, email, password).
        background_tasks (BackgroundTasks): Digunakan untuk mengirim email OTP secara async.
        session (AsyncSession): Sesi database async yang di-inject oleh FastAPI.

    Returns:
        dict[str, str]: Pesan konfirmasi bahwa OTP telah dikirim ke email.
    """
    return await up(data_in, session, background_tasks)


@router.post("/resend-otp")
async def resend_otp(
    data_in: OTP,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session_async),
) -> dict[str, str]:
    """
    Mengirim ulang kode OTP ke email pengguna yang belum terverifikasi.

    Args:
        data_in (OTP): Data berisi email pengguna.
        background_tasks (BackgroundTasks): Digunakan untuk mengirim email OTP secara async.
        session (AsyncSession): Sesi database async yang di-inject oleh FastAPI.

    Returns:
        dict[str, str]: Pesan konfirmasi bahwa OTP baru telah dikirim ke email.
    """
    return await ro(data_in, session, background_tasks)


@router.post("/verify")
async def verify(
    response: Response,
    data_in: VerifyOTP,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session_async),
) -> dict[str, str]:
    """
    Memverifikasi kode OTP yang dimasukkan pengguna untuk mengaktifkan akun.

    Jika OTP valid, akun akan diaktifkan dan pengguna langsung mendapatkan
    access token (login otomatis) melalui HTTPOnly cookie.

    Args:
        response (Response): Objek response FastAPI untuk menyimpan cookie token.
        data_in (VerifyOTP): Data berisi email dan kode OTP.
        background_tasks (BackgroundTasks): Digunakan untuk mengirim email selamat datang.
        session (AsyncSession): Sesi database async yang di-inject oleh FastAPI.

    Returns:
        dict[str, str]: Pesan konfirmasi bahwa login berhasil.
    """
    return await va(response, data_in.email, data_in.otp, session, background_tasks)


@router.post("/sign-in")
async def sign_in(
    response: Response,
    request: SignIn,
    session: AsyncSession = Depends(get_session_async),
) -> dict[str, str]:
    """
    Melakukan login pengguna menggunakan email dan password.

    Jika autentikasi berhasil, access token disimpan dalam HTTPOnly cookie.
    Akun yang belum terverifikasi tidak dapat login.

    Args:
        response (Response): Objek response FastAPI untuk menyimpan cookie token.
        request (SignIn): Data login berisi email dan password.
        session (AsyncSession): Sesi database async yang di-inject oleh FastAPI.

    Returns:
        dict[str, str]: Pesan konfirmasi bahwa login berhasil.
    """
    return await si(response, request, session)


@router.post("/forgot")
async def forgot(
    forgot_in: ForgotPassword,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session_async),
) -> dict[str, str]:
    """
    Mengirimkan link reset password ke email pengguna.

    Link yang dikirim mengandung JWT token bertipe 'reset_password'
    yang berlaku selama 1 jam.

    Args:
        forgot_in (ForgotPassword): 
            Data berisi email pengguna.
        background_tasks (BackgroundTasks): 
            Digunakan untuk mengirim email reset password secara async.
        session (AsyncSession): 
            Sesi database async yang di-inject oleh FastAPI.

    Returns:
        dict[str, str]: Pesan konfirmasi bahwa proses reset password berhasil dimulai.
    """
    await fp(forgot_in, session, background_tasks)
    return {"status": "success", "message": "success"}


@router.delete("/log-out")
async def log_out(
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_session_async),
) -> dict[str, str]:
    """
    Mengakhiri sesi pengguna (logout).

    Token aktif akan dimasukkan ke daftar hitam (blacklist) agar tidak bisa
    digunakan kembali, dan cookie 'access_token' akan dihapus dari browser.

    Args:
        response (Response): Objek response FastAPI untuk menghapus cookie.
        request (Request): Objek request FastAPI untuk membaca cookie yang ada.
        session (AsyncSession): Sesi database async yang di-inject oleh FastAPI.

    Returns:
        dict[str, str]: Pesan konfirmasi bahwa logout berhasil.
    """
    return await la(response, request, session)


@router.patch("/reset-password")
async def change(
    edit_in: ChangePassword, session: AsyncSession = Depends(get_session_async)
) -> dict[str, str]:
    """
    Mengubah password pengguna menggunakan token reset yang dikirim via email.

    Token harus bertipe 'reset_password' dan masih berlaku (belum kadaluwarsa).

    Args:
        edit_in (ChangePassword): Data berisi token reset dan password baru.
        session (AsyncSession): Sesi database async yang di-inject oleh FastAPI.

    Returns:
        dict[str, str]: Pesan konfirmasi bahwa password berhasil diubah.
    """
    await ea(edit_in, session)
    return {"status": "success", "messages": "None"}
