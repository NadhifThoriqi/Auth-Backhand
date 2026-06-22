# 🔐 Backend Auth API

Backend autentikasi berbasis **FastAPI** dengan fitur registrasi, verifikasi OTP via email, login, reset password, dan manajemen sesi menggunakan JWT + HTTPOnly Cookie.

---

## 📋 Fitur

- **Sign Up** — Registrasi akun baru dengan pengiriman OTP ke email
- **Verify OTP** — Aktivasi akun menggunakan kode OTP 6 digit
- **Resend OTP** — Kirim ulang kode OTP untuk akun yang belum terverifikasi
- **Sign In** — Login dengan email & password, token disimpan di HTTPOnly Cookie
- **Forgot Password** — Kirim link reset password ke email
- **Reset Password** — Ubah password menggunakan token reset
- **Logout** — Invalidasi token dengan sistem blacklist
- **Me** — Ambil data profil pengguna yang sedang login

---

## 🗂️ Struktur Proyek

```
.
├── main.py                         # Entry point aplikasi FastAPI
├── requirements.txt                # Daftar dependency Python
├── .env.example                    # Contoh konfigurasi environment
└── apps/
    ├── api/
    │   └── auth.py                 # Router & endpoint autentikasi
    ├── core/
    │   ├── enums.py                # Enumerasi (Role: admin, buyer)
    │   └── security.py             # JWT, hashing password, validasi token
    ├── db/
    │   └── sync_sessions.py        # Koneksi database async & session factory
    ├── models/
    │   └── auth.py                 # Model tabel: Auth, BlacklistToken
    ├── schemas/
    │   └── auth.py                 # Skema Pydantic untuk request/response
    └── services/
        ├── auth.py                 # Logika bisnis autentikasi
        ├── massages.py             # Layanan pengiriman email (FastAPI-Mail)
        └── templates/              # Template HTML email
            ├── general.html
            ├── otp.html
            ├── welcome.html
            └── reset_password.html
```

---

## ⚙️ Konfigurasi Environment

Salin file `.env.example` menjadi `.env` lalu sesuaikan isinya:

```bash
cp .env.example .env
```

| Variable        | Keterangan                                              | Contoh                                                     |
|-----------------|---------------------------------------------------------|------------------------------------------------------------|
| `DATABASE_URL`  | URL koneksi database async (asyncpg)                    | `postgresql+asyncpg://user:pass@localhost:5432/mydb`       |
| `SECRET_KEY`    | Kunci rahasia untuk signing JWT                         | `supersecretkey123`                                        |
| `HTTPS`         | `True` jika sudah pakai HTTPS (untuk flag secure cookie)| `False`                                                    |
| `DOMAIN`        | Domain frontend untuk link di email                     | `https://myapp.com`                                        |
| `MAIL_USERNAME` | Username akun Gmail pengirim                            | `bot@gmail.com`                                            |
| `MAIL_PASSWORD` | App Password Gmail (bukan password biasa)               | `xxxx xxxx xxxx xxxx`                                      |
| `MAIL_FROM`     | Alamat email pengirim yang ditampilkan                  | `bot@gmail.com`                                            |

> **Catatan:** Untuk `MAIL_PASSWORD`, gunakan **App Password** dari Google, bukan password akun Gmail biasa. Aktifkan di [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

---

## 🚀 Instalasi & Menjalankan

### 1. Clone repositori

```bash
git clone <url-repositori>
cd <nama-folder>
```

### 2. Buat virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependency

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi environment

```bash
cp .env.example .env
# Edit file .env sesuai konfigurasi Anda
```

### 5. Jalankan aplikasi

```bash
uvicorn main:app --reload
```

Aplikasi akan berjalan di `http://localhost:8000`

> Karena dikonfigurasi dengan `root_path="/thorix"`, dokumentasi Swagger tersedia di:
> `http://localhost:8000/thorix/docs`

---

## 📡 Daftar Endpoint

Base URL: `/auth`

| Method     | Endpoint              | Deskripsi                                          | Auth       |
|------------|-----------------------|----------------------------------------------------|------------|
| `GET`      | `/auth/me`            | Mengambil data profil pengguna yang login          | ✅ Required |
| `POST`     | `/auth/sign-up`       | Registrasi akun baru, kirim OTP ke email           | ❌          |
| `POST`     | `/auth/resend-otp`    | Kirim ulang OTP untuk akun belum terverifikasi     | ❌          |
| `POST`     | `/auth/verify`        | Verifikasi OTP & aktivasi akun (auto login)        | ❌          |
| `POST`     | `/auth/sign-in`       | Login dengan email & password                      | ❌          |
| `POST`     | `/auth/forgot`        | Kirim link reset password ke email                 | ❌          |
| `DELETE`   | `/auth/log-out`       | Logout & invalidasi token                          | ✅ Required |
| `PATCH`    | `/auth/reset-password`| Ubah password menggunakan token reset              | ❌          |

### Contoh Request & Response

#### POST `/auth/sign-up`
```json
// Request Body
{
  "name": "Budi Santoso",
  "email": "budi@example.com",
  "password": "password123"
}

// Response 200
{
  "status": "success",
  "message": "Kode verifikasi baru telah dikirim ke email Anda."
}
```

#### POST `/auth/verify`
```json
// Request Body
{
  "email": "budi@example.com",
  "otp": 482910
}

// Response 200
{
  "status": "success",
  "message": "Login berhasil"
}
```

#### POST `/auth/sign-in`
```json
// Request Body
{
  "email": "budi@example.com",
  "password": "password123"
}

// Response 200
{
  "status": "success",
  "message": "Login berhasil"
}
```

#### GET `/auth/me`
```json
// Response 200
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Budi Santoso",
  "email": "budi@example.com",
  "is_verified": true,
  "role": "buyer"
}
```

---

## 🔒 Mekanisme Keamanan

### JWT + HTTPOnly Cookie
Token disimpan dalam HTTPOnly Cookie sehingga tidak dapat diakses oleh JavaScript (proteksi XSS). Konfigurasi cookie:

| Parameter  | Nilai           | Keterangan                        |
|------------|-----------------|-----------------------------------|
| `httponly` | `True`          | Tidak bisa diakses JavaScript     |
| `samesite` | `lax`           | Proteksi dasar CSRF               |
| `max_age`  | `2592000` detik | Berlaku selama 30 hari            |
| `secure`   | Dari env `HTTPS`| `True` jika sudah pakai HTTPS     |

### Autentikasi Request
API mendukung dua metode pengiriman token:

1. **Cookie** (untuk Web Browser) — otomatis dikirim browser
2. **Authorization Header Bearer** (untuk Mobile/Postman):
   ```
   Authorization: Bearer <token>
   ```

### Token Blacklist
Saat logout, token dimasukkan ke tabel `blacklist_token` di database. Setiap request akan dicek terlebih dahulu apakah tokennya ada di blacklist sebelum diproses.

### Password Hashing
Password di-hash menggunakan **bcrypt** dengan salt acak sebelum disimpan ke database.

---

## 🗃️ Struktur Database

### Tabel `auth`

| Kolom             | Tipe           | Keterangan                               |
|-------------------|----------------|------------------------------------------|
| `id`              | UUID (PK)      | ID unik pengguna (auto-generated)        |
| `name`            | String         | Nama lengkap pengguna                    |
| `email`           | EmailStr       | Email unik, terindeks                    |
| `hashed_password` | String         | Password yang sudah di-hash (bcrypt)     |
| `is_verified`     | Boolean        | Status verifikasi OTP (default: `False`) |
| `otp_code`        | Integer / NULL | Kode OTP sementara, dihapus setelah verify |
| `role`            | Enum           | Peran pengguna: `admin` atau `buyer`     |

### Tabel `blacklist_token`

| Kolom            | Tipe      | Keterangan                             |
|------------------|-----------|----------------------------------------|
| `id`             | UUID (PK) | ID unik (auto-generated)               |
| `token`          | String    | Token JWT yang di-blacklist            |
| `blacklisted_at` | Timestamp | Waktu token dimasukkan ke blacklist    |

---

## 📦 Dependency Utama

| Package          | Kegunaan                                    |
|------------------|---------------------------------------------|
| `fastapi`        | Framework web async                         |
| `uvicorn`        | ASGI server                                 |
| `sqlmodel`       | ORM berbasis SQLAlchemy + Pydantic          |
| `asyncpg`        | Driver PostgreSQL async                     |
| `pyjwt`          | Pembuatan & validasi JWT token              |
| `bcrypt`         | Hashing password                            |
| `fastapi-mail`   | Pengiriman email via SMTP                   |
| `environs`       | Parsing environment variables               |
| `python-dotenv`  | Memuat file `.env`                          |