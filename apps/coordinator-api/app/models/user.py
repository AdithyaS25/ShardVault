"""
models/user.py — ShardLock Coordinator API
==========================================
DIFF from existing file:
  ADDED: vault_entries relationship (back_populates="user")
         Required now that VaultEntry has a FK to users.

Everything else is unchanged from the audited version.
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
    encryption_salt = Column(LargeBinary(32), nullable=True)

    created_at      = Column(DateTime, default=datetime.utcnow)

    refresh_tokens  = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # ── NEW: vault entries relationship ───────────────────────────────────────
    vault_entries   = relationship(
        "VaultEntry",
        back_populates="user",
        cascade="all, delete-orphan",
    )