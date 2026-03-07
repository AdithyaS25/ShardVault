"""
routes.py — app/crypto/
========================
FastAPI routes for the Encryption Engine.
Mirrors the pattern used in app/auth/routes.py.

Registered in main.py as:
    from app.crypto.routes import router as crypto_router
    app.include_router(crypto_router, prefix="/api/v1")

Endpoints:
    POST /api/v1/crypto/encrypt  — encrypt a secret (vault store flow)
    POST /api/v1/crypto/decrypt  — decrypt a secret (vault retrieve flow)
    GET  /api/v1/crypto/health   — engine self-test
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.crypto.encryption import (
    derive_encryption_key,
    encrypt_secret,
    decrypt_secret,
    generate_salt,
    payload_metadata,
    ARGON2_AVAILABLE,
)
from app.schemas.crypto import (
    EncryptRequest,
    EncryptResponse,
    DecryptRequest,
    DecryptResponse,
    CryptoHealthResponse,
)
from app.core.dependencies import get_current_user  # existing auth dependency

router = APIRouter(prefix="/crypto", tags=["Encryption Engine"])


# ── POST /crypto/encrypt ──────────────────────────────────────────────────────

@router.post(
    "/encrypt",
    response_model=EncryptResponse,
    status_code=status.HTTP_200_OK,
    summary="Encrypt a secret",
)
async def encrypt(
    body: EncryptRequest,
    current_user=Depends(get_current_user),
):
    """
    Encrypt a plaintext secret using AES-256-GCM.

    - Pass `salt_hex` if the user already has a salt in the DB (normal flow).
    - Omit `salt_hex` only during first vault entry for a new user — a fresh
      salt will be generated and returned for you to store in the users table.
    - Master password is never logged.
    """
    try:
        salt = bytes.fromhex(body.salt_hex) if body.salt_hex else generate_salt()

        key       = derive_encryption_key(body.master_password, salt)
        encrypted = encrypt_secret(body.plaintext, key)
        meta      = payload_metadata(encrypted)

        return EncryptResponse(
            encrypted_payload=encrypted,
            salt_hex=salt.hex(),
            algorithm="AES-256-GCM",
            payload_metadata=meta,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Encryption failed.",
        )


# ── POST /crypto/decrypt ──────────────────────────────────────────────────────

@router.post(
    "/decrypt",
    response_model=DecryptResponse,
    status_code=status.HTTP_200_OK,
    summary="Decrypt a secret",
)
async def decrypt(
    body: DecryptRequest,
    current_user=Depends(get_current_user),
):
    """
    Decrypt an AES-256-GCM payload.

    Returns 401 if the authentication tag fails — covers both wrong master
    password and tampered ciphertext. Master password is never logged.
    """
    try:
        salt      = bytes.fromhex(body.salt_hex)
        key       = derive_encryption_key(body.master_password, salt)
        plaintext = decrypt_secret(body.encrypted_payload, key)

        return DecryptResponse(plaintext=plaintext)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Decryption failed: invalid key or tampered payload.",
        )


# ── GET /crypto/health ────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=CryptoHealthResponse,
    summary="Crypto engine health check",
)
async def crypto_health():
    """Run an internal encrypt/decrypt self-test and return engine status."""
    try:
        salt    = generate_salt()
        key     = derive_encryption_key("healthcheck", salt)
        payload = encrypt_secret("ping", key)
        result  = decrypt_secret(payload, key)
        passed  = result == "ping"
    except Exception:
        passed = False

    return CryptoHealthResponse(
        status="ok" if passed else "degraded",
        algorithm="AES-256-GCM",
        kdf="Argon2id" if ARGON2_AVAILABLE else "PBKDF2-SHA256",
        test_passed=passed,
    )