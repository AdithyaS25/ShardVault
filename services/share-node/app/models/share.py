"""
models/share.py — Share Node Service
======================================
Database model for storing a single secret share.

Each share node stores one row per vault entry.
The share contains only a fragment of the encrypted payload —
never the full secret, never the master password.

Per §2.3: shares are indexed by vault_entry_id and x_index (1-4).
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Share(Base):
    __tablename__ = "shares"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which vault entry this share belongs to (coordinator's vault_entry_id)
    vault_entry_id = Column(String, nullable=False, index=True, unique=True)

    # x-index of this share in the Shamir scheme (1-4)
    # This node always stores the same x_index (its NODE_ID determines which)
    x_index        = Column(Integer, nullable=False)

    # The y-bytes of the share encoded as base64 string
    y_value        = Column(Text, nullable=False)

    # When this share was stored
    created_at     = Column(DateTime, default=datetime.utcnow)