"""
schemas/shamir.py — ShardLock Coordinator API
==============================================
Pydantic request/response schemas for the Secret Sharing Engine.
Mirrors the pattern used in schemas/auth.py and schemas/crypto.py.
"""

from pydantic import BaseModel, Field
from typing import List
import uuid


# ── Split ─────────────────────────────────────────────────────────────────────

class SplitRequest(BaseModel):
    encrypted_payload: str = Field(
        ...,
        description="Base64 AES-256-GCM payload from POST /crypto/encrypt",
    )
    vault_entry_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Vault entry UUID — used to index shares at share nodes",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "encrypted_payload": "base64encodedpayload==",
                "vault_entry_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }


class SplitResponse(BaseModel):
    shares: List[dict] = Field(
        ...,
        description='N=4 share dicts: [{"x": int, "y": "base64"}, ...]',
    )
    total_shares: int = Field(..., description="N — total shares generated")
    threshold: int = Field(..., description="K — minimum shares for reconstruction")
    secret_length: int = Field(..., description="Byte length of secret — store in vault_entries")
    vault_entry_id: str


# ── Reconstruct ───────────────────────────────────────────────────────────────

class ReconstructRequest(BaseModel):
    shares: List[dict] = Field(
        ...,
        min_length=3,
        description='At least K=3 share dicts: [{"x": int, "y": "base64"}, ...]',
    )
    secret_length: int = Field(
        ...,
        description="Byte length from vault_entries metadata — required for reconstruction",
    )
    vault_entry_id: str = Field(
        ...,
        description="Vault entry UUID for audit logging",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "shares": [
                    {"x": 1, "y": "base64share1=="},
                    {"x": 2, "y": "base64share2=="},
                    {"x": 3, "y": "base64share3=="},
                ],
                "secret_length": 44,
                "vault_entry_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }


class ReconstructResponse(BaseModel):
    encrypted_payload: str = Field(
        ...,
        description="Reconstructed Base64 payload — pass to POST /crypto/decrypt",
    )
    shares_used: int
    threshold: int
    vault_entry_id: str


# ── Health / Config ───────────────────────────────────────────────────────────

class ShamirHealthResponse(BaseModel):
    status: str
    total_shares: int
    threshold: int
    test_passed: bool


class ShamirConfigResponse(BaseModel):
    total_shares: int
    threshold: int
    field: str
    irreducible_polynomial: str