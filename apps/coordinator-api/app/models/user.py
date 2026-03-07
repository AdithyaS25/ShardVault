"""
models/user.py — ShardLock Coordinator API
==========================================
User database model.

FIX APPLIED:
  - Added `salt` column (LargeBinary, 32 bytes) per §2.1 database schema.
    This salt is generated once at registration and stored here.
    The Encryption Engine uses it for Argon2id key derivation.
    Without it, vault encryption/decryption cannot function.

  - Added `encryption_salt` as the column name to be explicit about
    its purpose (separate from any auth-related salts).
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email           = Column(String, unique=True, nullable=False, index=True)
    password_hash   = Column(String, nullable=False)
    role            = Column(String, default="user", nullable=False)

    # Per §2.1 and §2.2: per-user salt for AES-256-GCM key derivation
    # Generated once at registration via generate_salt(), never changes
    encryption_salt = Column(LargeBinary(32), nullable=True)  # nullable for existing users

    created_at      = Column(DateTime, default=datetime.utcnow)

    refresh_tokens  = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )