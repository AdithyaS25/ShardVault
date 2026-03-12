"""
models/vault_entry.py — ShardLock Coordinator API
===================================================
VaultEntry database model.

Stores metadata only — never the plaintext password or full encrypted payload.
The encrypted payload is split into shares distributed across share nodes (§2.3).

Per §2.1 database schema:
  - UUID primary key
  - Foreign key to users with cascade delete
  - Stores encrypted_payload length (needed for Shamir reconstruction)
  - Stores the site/label/username for display in vault list

Per §2.2 / §2.3 design:
  - encrypted_payload_length: needed by reconstruct_secret() to know
    how many bytes to expect when reassembling shares
  - No plaintext, no master password, no full ciphertext stored here
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class VaultEntry(Base):
    __tablename__ = "vault_entries"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Display metadata — shown in vault list
    site_name   = Column(String, nullable=False)
    username    = Column(String, nullable=False)
    label       = Column(String, nullable=True)   # optional friendly label

    # Required for Shamir reconstruction (§2.3)
    # reconstruct_secret() needs the exact byte length of the original secret
    encrypted_payload_length = Column(Integer, nullable=False)

    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to user
    user        = relationship("User", back_populates="vault_entries")