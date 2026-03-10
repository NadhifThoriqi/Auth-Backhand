from pydantic import BaseModel, EmailStr, field_validator

import re

class SignInAuth(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        # 1. Cek Panjang Minimal
        if len(v) < 8:
            raise ValueError("Password minimal harus 8 karakter.")
        
        # 2. Cek Huruf Besar
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password harus mengandung setidaknya satu huruf besar.")
        
        # 3. Cek Huruf Kecil
        if not re.search(r"[a-z]", v):
            raise ValueError("Password harus mengandung setidaknya satu huruf kecil.")
        
        # 4. Cek Angka
        if not re.search(r"\d", v):
            raise ValueError("Password harus mengandung setidaknya satu angka.")
        
        # 5. Cek Simbol/Karakter Khusus
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password harus mengandung setidaknya satu simbol khusus.")
            
        return v