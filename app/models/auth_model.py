from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String
from pydantic import EmailStr
from typing import Optional
from app.db.config import GUID
from datetime import datetime, timezone
import uuid

class Auth(SQLModel, table=True):
    __tablename__ = "auth"
    
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, # Gunakan default_factory untuk fungsi
        sa_column=Column(GUID(), primary_key=True, index=True, unique=True)
    )
    email: EmailStr = Field(
        sa_column=Column(String(255), index=True, unique=True, nullable=False)
    )
    hashed_password: str = Field(
        nullable=False
    )

class BlacklistToken(SQLModel, table=True):
    __tablename__ = "blacklist_token" # Sesuaikan dengan nama tabel di MySQL kamu
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, # Gunakan default_factory untuk fungsi
        sa_column=Column(GUID(), primary_key=True, index=True, unique=True)
    )
    token: str = Field(
        sa_column=Column(String(500), index=True, unique=True, nullable=False)
    )
    blacklisted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
