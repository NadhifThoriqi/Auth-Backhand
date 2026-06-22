"""
Module:
    db/sync_sessions.py
Deskripsi:
    Mengatur koneksi database asynchronous menggunakan SQLModel dan SQLAlchemy.
    Menyediakan engine, session factory, dan fungsi-fungsi helper untuk
    interaksi dengan database.
"""

from typing import Any

from dotenv import load_dotenv
from environs import Env
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

load_dotenv()
env = Env()
mysql_url = env.str("DATABASE_URL")

if not mysql_url:
    raise RuntimeError("DATABASE_URL Tidak dapat ditemukan di environment variables!")

engine = create_async_engine(mysql_url, echo=True)

# Membuat session khusus async
ASYNC_SESSION_LOCAL = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    """
    Menginisialisasi database dengan membuat semua tabel yang belum ada.

    Menggunakan metadata SQLModel (yang di balik layar menggunakan SQLAlchemy)
    untuk membuat tabel secara otomatis berdasarkan definisi model yang ada.
    Engine di-dispose setelah proses selesai untuk melepaskan koneksi sementara.
    """
    async with engine.begin() as conn:
        # SQLModel menggunakan metadata SQLAlchemy di latar belakang
        # .run_sync() diperlukan karena metadata.create_all adalah fungsi sinkron
        await conn.run_sync(SQLModel.metadata.create_all)

    # Tutup engine setelah selesai jika tidak digunakan lagi
    await engine.dispose()


# Generator dependency async untuk FastAPI
async def get_session_async():
    """
    Generator dependency untuk menyediakan sesi database async ke endpoint FastAPI.

    Digunakan bersama `Depends()` di endpoint agar setiap request mendapatkan
    sesi database yang terisolasi dan otomatis ditutup setelah request selesai.

    Yields:
        AsyncSession: Sesi database async yang aktif.
    """
    async with ASYNC_SESSION_LOCAL() as session:
        yield session


async def save_db(session: AsyncSession, model_object: Any):
    """
    Menyimpan atau memperbarui objek model ke database dan me-refresh datanya.

    Fungsi ini menggabungkan tiga operasi umum menjadi satu:
    add → commit → refresh, sehingga objek yang dikembalikan selalu
    mencerminkan data terbaru dari database (termasuk nilai auto-generated).

    Args:
        session (AsyncSession): Sesi database async yang aktif.
        model_object (Any): Objek model SQLModel yang akan disimpan atau diperbarui.

    Returns:
        Any: Objek model yang sama setelah di-refresh dari database.
    """
    session.add(model_object)
    await session.commit()
    await session.refresh(model_object)
    return model_object
