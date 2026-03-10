from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Import package api
from app import api
from app.api import auth
from app.core.limiter import limiter
from app.db.session import create_db_and_tables

import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # --- DIJALANKAN SAAT STARTUP ---
    print("Aplikasi sedang berjalan, membuat tabel...")
    
    # Membuat database & tabel jika belum ada
    create_db_and_tables()
    
    # Aplikasi mulai menerima request setelah ini
    yield
    
    # --- DIJALANKAN SAAT SHUTDOWN ---
    print("Aplikasi sedang dimatikan...")
    
# PENTING: Tambahkan root_path agar sinkron dengan Nginx /thorix/
app = FastAPI(root_path="/thorix", lifespan=lifespan) 

address = [
    "http://localhost:5500",
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=address,
    allow_credentials=True,
    allow_methods=["DELETE", "GET", "POST", "PUT"],
    allow_headers=["*"],
)

# 1. Sambungkan Limiter ke State App (WAJIB)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Root route untuk testing apakah aplikasi sudah "up"
@app.get("/")
def read_root():
    return {"status": "FastAPI is running", "path": "/thorix/"}

# Loop Dynamic Router
# for _, module_name, _ in pkgutil.iter_modules(api.__path__):
#     # Import modul secara dinamis
#     module = importlib.import_module(f"app.api.{module_name}")
    
#     # Cek apakah di dalam file (misal users.py) ada variabel 'router'
#     if hasattr(module, "router"):
#         app.include_router(module.router)
    
# Static Router
app.include_router(auth.router)

if __name__ == "__main__":
    # Host 0.0.0.0 agar bisa diakses oleh Nginx
    uvicorn.run("main:app", host='127.0.0.1', port=2001, reload=True)
