import multiprocessing
from environs import Env
from gunicorn.arbiter import Arbiter
from gunicorn.workers.base import Worker

# ==============================================================
# Konfigurasi Gunicorn dengan Uvicorn Worker
# ==============================================================

env = Env()
env.read_env()

# Alamat & Port
bind = env.str("BIND", default="0.0.0.0:8000")

# Worker Class — Uvicorn untuk support async FastAPI
worker_class = "uvicorn.workers.UvicornWorker"

# Jumlah Worker: (2 x CPU) + 1 adalah rumus umum
workers = env.int("WORKERS", default=multiprocessing.cpu_count() * 2 + 1)

# Thread per worker (untuk UvicornWorker biasanya 1)
threads = env.int("THREADS", default=1)

# Timeout (detik) — naikkan jika ada request berat
timeout = env.int("TIMEOUT", default=120)

# Graceful timeout saat shutdown
graceful_timeout = env.int("GRACEFUL_TIMEOUT", default=30)

# Keep-alive connection
keepalive = env.int("KEEPALIVE", default=5)

# Maksimum request per worker sebelum restart (mencegah memory leak)
max_requests = env.int("MAX_REQUESTS", default=1000)
max_requests_jitter = env.int("MAX_REQUESTS_JITTER", default=50)

# Logging
loglevel = env.str("LOG_LEVEL", default="info")
accesslog = env.str("ACCESS_LOG", default="-")   # "-" = stdout
errorlog = env.str("ERROR_LOG", default="-")     # "-" = stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Preload app untuk menghemat memori (fork setelah import)
preload_app = env.bool("PRELOAD_APP", default=True)

# Reload otomatis saat kode berubah (hanya untuk development)
reload = env.bool("RELOAD", default=False)

# ==============================================================
# Hooks — Event Lifecycle
# ==============================================================

def on_starting(server: Arbiter):
    print("=" * 50)
    print("🚀 Gunicorn + Uvicorn mulai berjalan...")
    print(f"   Workers : {workers}")
    print(f"   Bind    : {bind}")
    print(f"   Timeout : {timeout}s")
    print("=" * 50)

def on_exit(server: Arbiter):
    print("🛑 Gunicorn berhenti.")

def worker_init(worker: Worker):
    print(f"✅ Worker {worker.pid} siap melayani request")

def worker_exit(worker: Worker, server: Arbiter):
    print(f"❌ Worker {worker.pid} berhenti")
