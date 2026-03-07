"""
schemas/crypto.py — ShardLock Coordinator API
==============================================
Pydantic request/response schemas for the Encryption Engine.
Mirrors the pattern used in schemas/auth.py.
"""

from pydantic import BaseModel, Field


# ── Encrypt ───────────────────────────────────────────────────────────────────

class EncryptRequest(BaseModel):
    plaintext: str = Field(
        ...,
        min_length=1,
        description="The secret/password to encrypt",
    )
    master_password: str = Field(
        ...,
        min_length=8,
        description="User's master password — used for key derivation, never stored",
    )
    salt_hex: str | None = Field(
        None,
        description=(
            "Hex-encoded per-user salt from the users table. "
            "Omit only on first vault entry — a new salt will be returned."
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "plaintext": "my-gmail-password-123",
                "master_password": "my_master_pass",
                "salt_hex": "a3f1...",
            }
        }


class EncryptResponse(BaseModel):
    encrypted_payload: str = Field(
        ...,
        description="Base64-encoded AES-256-GCM payload — store in vault_entries table",
    )
    salt_hex: str = Field(
        ...,
        description="Hex salt — store in users table if this was newly generated",
    )
    algorithm: str = Field(default="AES-256-GCM")
    payload_metadata: dict


# ── Decrypt ───────────────────────────────────────────────────────────────────

class DecryptRequest(BaseModel):
    encrypted_payload: str = Field(
        ...,
        description="Base64-encoded payload from the encrypt endpoint",
    )
    master_password: str = Field(
        ...,
        min_length=8,
        description="User's master password",
    )
    salt_hex: str = Field(
        ...,
        description="Hex-encoded per-user salt from the users table",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "encrypted_payload": "base64string...",
                "master_password": "my_master_pass",
                "salt_hex": "a3f1...",
            }
        }


class DecryptResponse(BaseModel):
    plaintext: str = Field(..., description="The original decrypted secret")


# ── Health ────────────────────────────────────────────────────────────────────

class CryptoHealthResponse(BaseModel):
    status: str = Field(..., description="'ok' or 'degraded'")
    algorithm: str
    kdf: str = Field(..., description="Key derivation function in use")
    test_passed: bool