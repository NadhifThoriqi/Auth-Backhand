from slowapi import Limiter
from slowapi.util import get_remote_address

# Inisialisasi limiter di sini agar bisa dipakai bersama
limiter = Limiter(key_func=get_remote_address)