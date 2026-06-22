"""
Module:
    main.py
Deskripsi:
    Entry point aplikasi FastAPI.
    Menginisialisasi aplikasi, mengatur middleware CORS,
    mendaftarkan router, dan mengelola lifecycle aplikasi (startup & shutdown).
Author:
    Nadhif Thoriqi
"""

from contextlib import asynccontextmanager

from apps.api import auth
from apps.db.async_sessions import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(life_app: FastAPI):
    """
    Konteks manajer lifecycle aplikasi FastAPI.

    Dijalankan saat startup:
        - Mencetak nama aplikasi yang sedang berjalan.
        - Menginisialisasi database (membuat tabel jika belum ada).

    Dijalankan saat shutdown:
        - Mencetak pesan bahwa aplikasi sedang dimatikan.

    Args:
        life_app (FastAPI): Instance aplikasi FastAPI yang sedang berjalan.
    """
    # --- DIJALANKAN SAAT STARTUP ---
    # Menggunakan 'life_app' agar tidak kena error W0613 (Unused argument)
    print(f"Aplikasi {life_app.title} sedang berjalan...")

    await init_db()
    yield

    # --- DIJALANKAN SAAT SHUTDOWN ---
    print("Aplikasi sedang dimatikan...")


# PENTING: Tambahkan root_path agar sinkron dengan Nginx /thorix/
app = FastAPI(root_path="/thorix", lifespan=lifespan)

ORIGINS = "http://localhost:9876"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ORIGINS],
    allow_credentials=True,
    allow_methods=["DELETE", "GET", "POST", "PUT", "PATCH"],
    allow_headers=["*"],
)


# Root route untuk testing apakah aplikasi sudah "up"
@app.get("/")
def read_root():
    """
    Endpoint root untuk mengecek apakah aplikasi sudah aktif.

    Returns:
        dict: Status aplikasi dan path root yang dikonfigurasi.
    """
    return {"status": "FastAPI is running", "path": "/thorix/"}


@app.get("/health")
def health_check():
    """
    Endpoint health check untuk monitoring ketersediaan layanan.

    Returns:
        dict: Status kesehatan aplikasi dengan nilai "ok".
    """
    return {"status": "ok"}


app.include_router(auth.router)

# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)  # nosec
