"""
schemas/share.py — Share Node Service
======================================
Request/response schemas for internal share node API (§2.4).
"""

from pydantic import BaseModel, Field
from datetime import datetime


# ── Store Share ───────────────────────────────────────────────────────────────

class StoreShareRequest(BaseModel):
    vault_entry_id: str = Field(
        ...,
        description="Vault entry UUID from the coordinator",
    )
    x_index: int = Field(
        ...,
        ge=1,
        le=4,
        description="Share x-index in the Shamir scheme (1-4)",
    )
    y_value: str = Field(
        ...,
        description="Base64-encoded y-bytes of this share",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "vault_entry_id": "550e8400-e29b-41d4-a716-446655440000",
                "x_index": 1,
                "y_value": "base64encodedshare==",
            }
        }


class StoreShareResponse(BaseModel):
    success: bool
    vault_entry_id: str
    node_id: str
    message: str


# ── Retrieve Share ────────────────────────────────────────────────────────────

class RetrieveShareResponse(BaseModel):
    vault_entry_id: str
    x_index: int
    y_value: str
    node_id: str
    created_at: datetime


# ── Delete Share ──────────────────────────────────────────────────────────────

class DeleteShareResponse(BaseModel):
    success: bool
    vault_entry_id: str
    node_id: str
    message: str