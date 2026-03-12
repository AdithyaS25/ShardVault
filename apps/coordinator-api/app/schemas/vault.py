"""
schemas/vault.py — ShardLock Coordinator API
=============================================
Pydantic schemas for vault management endpoints.

Mirrors the pattern in schemas/auth.py — request/response pairs
per endpoint, all inheriting from BaseModel.

Per §1.3 Standard API Response Contract:
  - Success: success=True, data object, message
  - Error: handled via HTTPException (success=False, error code, message)
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


# ── Create Vault ──────────────────────────────────────────────────────────────

class VaultCreateRequest(BaseModel):
    site_name       : str  = Field(..., min_length=1, max_length=255)
    username        : str  = Field(..., min_length=1, max_length=255)
    plaintext_password: str = Field(..., min_length=1)
    master_password : str  = Field(..., min_length=1)
    label           : Optional[str] = Field(None, max_length=255)


class VaultCreateResponse(BaseModel):
    success         : bool
    message         : str
    vault_id        : str


# ── List Vaults ───────────────────────────────────────────────────────────────

class VaultEntryMeta(BaseModel):
    """Single vault entry metadata — no passwords, no encrypted data."""
    id          : UUID
    site_name   : str
    username    : str
    label       : Optional[str]
    created_at  : datetime
    updated_at  : datetime

    class Config:
        from_attributes = True


class VaultListResponse(BaseModel):
    success     : bool
    data        : List[VaultEntryMeta]
    total       : int
    page        : int
    page_size   : int


# ── Get Single Vault (triggers reconstruction) ────────────────────────────────

class VaultRetrieveResponse(BaseModel):
    success             : bool
    vault_id            : str
    site_name           : str
    username            : str
    label               : Optional[str]
    plaintext_password  : str   # decrypted, returned to client — never stored


# ── Delete Vault ──────────────────────────────────────────────────────────────

class VaultDeleteResponse(BaseModel):
    success : bool
    message : str