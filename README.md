# 🔐 FastAPI Auth Service

Backend layanan autentikasi berbasis **FastAPI** dengan dukungan database **PostgreSQL** (kompatibel dengan Supabase), JWT token, OTP via email, dan arsitektur async penuh.

> **Author:** Nadhif Thoriqi

---

## 📋 Daftar Isi

- [Fitur](#-fitur)
- [Teknologi](#-teknologi)
- [Struktur Proyek](#-struktur-proyek)
- [Instalasi](#-instalasi)
- [Konfigurasi Environment](#-konfigurasi-environment)
- [Menjalankan Aplikasi](#-menjalankan-aplikasi)
- [API Endpoints](#-api-endpoints)
- [Arsitektur & Alur Kerja](#-arsitektur--alur-kerja)
- [Keamanan](#-keamanan)

---

## ✨ Fitur

- ✅ **Registrasi akun** dengan verifikasi OTP via email
- ✅ **Login** dengan email & password, token disimpan di HTTPOnly Cookie
- ✅ **Kirim ulang OTP** untuk akun yang belum terverifikasi
- ✅ **Lupa password** dengan link reset via email (token 1 jam)
- ✅ **Reset password** menggunakan token JWT khusus
- ✅ **Profil pengguna** (`/me`) untuk mendapatkan data user aktif
- ✅ **Logout** dengan mekanisme blacklist token
- ✅ **Sistem role** pengguna (`admin` / `buyer`)
- ✅ **Async penuh** menggunakan `asyncpg` + SQLModel
- ✅ **Email template HTML** untuk OTP, selamat datang, dan reset password

---

## 🛠 Teknologi

| Komponen | Teknologi |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Server (Dev) | [Uvicorn](https://www.uvicorn.org/) |
| Server (Prod) | [Gunicorn](https://gunicorn.org/) + Uvicorn Worker |
| ORM | [SQLModel](https://sqlmodel.tiangolo.com/) + SQLAlchemy Async |
| Database | PostgreSQL (via `asyncpg`) |
| Autentikasi | [PyJWT](https://pyjwt.readthedocs.io/) (algoritma HS256) |
| Hashing Password | [bcrypt](https://pypi.org/project/bcrypt/) |
| Email | [fastapi-mail](https://sabuhish.github.io/fastapi-mail/) |
| Konfigurasi | [environs](https://github.com/sloria/environs) + python-dotenv |

---

## 📁 Struktur Proyek

```
uji_supabase/
├── apps/
│   ├── api/
│   │   └── auth.py          # Routing & endpoint HTTP autentikasi
│   ├── core/
│   │   ├── enums.py         # Enum Role (ADMIN, BUYER)
│   │   └── security.py      # JWT, hashing password, validasi token
│   ├── db/
│   │   └── async_sessions.py # Engine, session async, helper save_db
│   ├── models/
│   │   └── auth.py          # Model tabel: Auth, BlacklistToken
│   ├── schemas/
│   │   └── auth.py          # Skema Pydantic (request/response DTO)
│   └── services/
│       ├── auth.py          # Logika bisnis autentikasi
│       ├── messages.py      # Layanan pengiriman email
│       └── templates/       # Template email HTML
│           ├── otp.html
│           ├── welcome.html
│           ├── reset_password.html
│           └── general.html
├── main.py                  # Entry point FastAPI
├── gunicorn.conf.py         # Konfigurasi Gunicorn production
├── Makefile                 # Shortcut perintah umum
├── requirements.txt         # Daftar dependensi Python
└── .env.example             # Contoh file konfigurasi environment
```

---

## 🚀 Instalasi

### Prasyarat

- Python 3.12+
- PostgreSQL (atau akun Supabase)
- Akun Gmail dengan [App Password](https://myaccount.google.com/apppasswords) aktif

### Langkah-langkah

**1. Clone repositori & masuk ke direktori proyek**
```bash
git clone <url-repo>
cd uji_supabase
```

**2. Buat dan aktifkan virtual environment**
```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

**3. Install dependensi**
```bash
make install
# atau
pip install -r requirements.txt
```

**4. Buat file `.env` dari template**
```bash
cp .env.example .env
```

**5. Isi konfigurasi di file `.env`** (lihat bagian [Konfigurasi Environment](#-konfigurasi-environment))

---

## ⚙️ Konfigurasi Environment

Salin `.env.example` menjadi `.env` lalu sesuaikan nilainya:

```env
# ==============================================================================
# 1. KONEKSI DATABASE
# ==============================================================================
DATABASE_URL="postgresql+asyncpg://user:password@host:port/database"

# ==============================================================================
# 2. KEAMANAN & KONFIGURASI APLIKASI
# ==============================================================================
SECRET_KEY="ganti-dengan-secret-key-yang-kuat-dan-panjang"
HTTPS=False
DOMAIN="http://localhost:5500"   # Domain frontend Anda

# ==============================================================================
# 3. PENGATURAN EMAIL (SMTP GMAIL)
# ==============================================================================
# Petunjuk mendapatkan MAIL_PASSWORD:
#   1. Aktifkan 2FA di Akun Google > Keamanan > Autentikasi 2 Langkah.
#   2. Buat "App Password", salin kode 16 digit yang muncul.
MAIL_USERNAME="email@gmail.com"
MAIL_PASSWORD="xxxx xxxx xxxx xxxx"  # App Password 16 digit
MAIL_FROM="email@gmail.com"

# ==============================================================================
# 4. SERVER WEB (GUNICORN + UVICORN)
# ==============================================================================
BIND=0.0.0.0:8000
TIMEOUT=120
GRACEFUL_TIMEOUT=30
KEEPALIVE=5
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=50
LOG_LEVEL=info
ACCESS_LOG=-
ERROR_LOG=-
PRELOAD_APP=true
RELOAD=false
# WORKERS=5   # Kosongkan untuk mengikuti jumlah core CPU otomatis
```

> **Tips:** Gunakan `python -c "import secrets; print(secrets.token_hex(32))"` untuk membuat `SECRET_KEY` yang kuat.

---

## ▶️ Menjalankan Aplikasi

### Mode Development (Hot Reload)
```bash
make dev
```
Aplikasi akan berjalan di `http://localhost:8000` dengan auto-reload aktif.

### Mode Production (Gunicorn)
```bash
make prod
```

### Mode Production dengan Override CLI
```bash
make prod-custom
```

### Akses Dokumentasi API
Setelah aplikasi berjalan, buka di browser:
- **Swagger UI:** `http://localhost:8000/thorix/docs`
- **ReDoc:** `http://localhost:8000/thorix/redoc`

---

## 📡 API Endpoints

Semua endpoint berada di bawah prefix `/auth`.

| Method | Endpoint | Deskripsi | Auth |
|---|---|---|---|
| `GET` | `/auth/me` | Mengambil data pengguna yang sedang login | ✅ Required |
| `POST` | `/auth/sign-up` | Mendaftar akun baru & kirim OTP ke email | ❌ |
| `POST` | `/auth/resend-otp` | Kirim ulang kode OTP | ❌ |
| `POST` | `/auth/verify` | Verifikasi OTP untuk mengaktifkan akun | ❌ |
| `POST` | `/auth/sign-in` | Login dengan email & password | ❌ |
| `POST` | `/auth/forgot` | Kirim link reset password ke email | ❌ |
| `DELETE` | `/auth/log-out` | Logout & hapus session | ✅ Required |
| `PATCH` | `/auth/reset-password` | Ubah password menggunakan token reset | ❌ |

### Contoh Request

**Registrasi (`POST /auth/sign-up`)**
```json
{
  "name": "Nadhif Thoriqi",
  "email": "nadhif@example.com",
  "password": "password123"
}
```

**Login (`POST /auth/sign-in`)**
```json
{
  "email": "nadhif@example.com",
  "password": "password123"
}
```

**Verifikasi OTP (`POST /auth/verify`)**
```json
{
  "email": "nadhif@example.com",
  "otp": 123456
}
```

**Reset Password (`PATCH /auth/reset-password`)**
```json
{
  "token": "<token_dari_email>",
  "password": "password_baru"
}
```

---

## 🏗 Arsitektur & Alur Kerja

### Alur Registrasi
```
Client → POST /sign-up → Cek email di DB
    ├── Email sudah terverifikasi → ❌ 400 Error
    ├── Email ada tapi belum verifikasi → Update OTP baru
    └── Email baru → Buat akun baru
              ↓
         Hash password → Simpan ke DB → Kirim OTP via email (background)
```

### Alur Login
```
Client → POST /sign-in → Cari user by email
    ├── Tidak ditemukan / password salah → ❌ 401 Unauthorized
    ├── Belum verifikasi OTP → ❌ 403 Forbidden
    └── Valid → Generate JWT (30 hari) → Set HTTPOnly Cookie
```

### Alur Logout
```
Client → DELETE /log-out → Baca token dari Cookie
    └── Simpan token ke tabel BlacklistToken → Hapus Cookie
```

### Struktur Token JWT

Token akses (`type: access`) memuat:
```json
{
  "sub": "uuid-user",
  "email": "user@example.com",
  "name": "Nama User",
  "type": "access",
  "exp": 1234567890
}
```

Token reset password (`type: reset_password`) berlaku **1 jam** dan hanya bisa digunakan di endpoint `/reset-password`.

---

## 🔒 Keamanan

| Fitur | Implementasi |
|---|---|
| **Hashing password** | bcrypt dengan salt otomatis |
| **JWT** | Algoritma HS256, masa berlaku 30 hari (access) / 1 jam (reset) |
| **Cookie** | HTTPOnly, SameSite=Lax — proteksi XSS & CSRF |
| **Token Blacklist** | Token yang logout disimpan di DB & ditolak saat digunakan kembali |
| **OTP** | 6 digit, di-generate dengan `secrets.randbelow` (kriptografis aman) |
| **Validasi tipe token** | Token login dan reset password dibedakan via field `type` |

---

## 🧹 Perintah Lainnya

```bash
# Menjalankan test
make test

# Membersihkan file cache Python
make clean
```

---

## 📄 Lisensi

Proyek ini dibuat untuk keperluan pembelajaran dan pengembangan. Silakan digunakan dan dimodifikasi sesuai kebutuhan.