"""
routes.py — app/shamir/
========================
FastAPI routes for the Secret Sharing Engine.
Mirrors the pattern used in app/auth/routes.py and app/crypto/routes.py.

Registered in main.py as:
    from app.shamir.routes import router as shamir_router
    app.include_router(shamir_router, prefix="/api/v1")

Endpoints:
    POST /api/v1/shamir/split        — split encrypted payload into N=4 shares
    POST /api/v1/shamir/reconstruct  — reconstruct payload from K>=3 shares
    GET  /api/v1/shamir/health       — engine self-test
    GET  /api/v1/shamir/config       — return N/K configuration
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.shamir.shamir import (
    split_encrypted_payload,
    reconstruct_encrypted_payload,
    split_secret,
    reconstruct_secret,
    TOTAL_SHARES,
    THRESHOLD,
)
from app.schemas.shamir import (
    SplitRequest,
    SplitResponse,
    ReconstructRequest,
    ReconstructResponse,
    ShamirHealthResponse,
    ShamirConfigResponse,
)
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/shamir", tags=["Secret Sharing Engine"])


# ── POST /shamir/split ────────────────────────────────────────────────────────

@router.post(
    "/split",
    response_model=SplitResponse,
    status_code=status.HTTP_200_OK,
    summary="Split encrypted payload into shares",
)
async def split(
    body: SplitRequest,
    current_user=Depends(get_current_user),
):
    """
    Split an AES-256-GCM encrypted_payload into N=4 Shamir shares.

    Vault creation flow:
      1. Client calls POST /crypto/encrypt → gets encrypted_payload
      2. Client calls POST /shamir/split   → gets 4 shares
      3. Coordinator distributes 1 share to each share node

    The encrypted_payload is never stored in the database — only shares
    are stored at share nodes. The DB stores only metadata (§2.1).
    """
    try:
        import base64
        secret_bytes  = base64.b64decode(body.encrypted_payload.encode("utf-8"))
        secret_length = len(secret_bytes)
        share_dicts   = split_encrypted_payload(body.encrypted_payload)

        return SplitResponse(
            shares=share_dicts,
            total_shares=TOTAL_SHARES,
            threshold=THRESHOLD,
            secret_length=secret_length,
            vault_entry_id=body.vault_entry_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Split failed: {str(e)}",
        )


# ── POST /shamir/reconstruct ──────────────────────────────────────────────────

@router.post(
    "/reconstruct",
    response_model=ReconstructResponse,
    status_code=status.HTTP_200_OK,
    summary="Reconstruct encrypted payload from shares",
)
async def reconstruct(
    body: ReconstructRequest,
    current_user=Depends(get_current_user),
):
    """
    Reconstruct encrypted_payload from K>=3 shares.

    Vault retrieval flow:
      1. Coordinator fetches shares from K=3 share nodes
      2. Client calls POST /shamir/reconstruct → gets encrypted_payload back
      3. Client calls POST /crypto/decrypt     → gets original plaintext secret

    Returns 422 if fewer than K=3 shares are provided (threshold not met).
    """
    if len(body.shares) < THRESHOLD:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Threshold not met: need at least {THRESHOLD} shares, got {len(body.shares)}",
        )

    try:
        encrypted_payload = reconstruct_encrypted_payload(
            share_dicts=body.shares,
            secret_length=body.secret_length,
        )

        return ReconstructResponse(
            encrypted_payload=encrypted_payload,
            shares_used=len(body.shares),
            threshold=THRESHOLD,
            vault_entry_id=body.vault_entry_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Reconstruction failed.",
        )


# ── GET /shamir/config ────────────────────────────────────────────────────────

@router.get(
    "/config",
    response_model=ShamirConfigResponse,
    summary="Return N/K configuration",
)
async def shamir_config():
    """Return the current N-of-K configuration."""
    return ShamirConfigResponse(
        total_shares=TOTAL_SHARES,
        threshold=THRESHOLD,
        field="GF(2^8)",
        irreducible_polynomial="x^8 + x^4 + x^3 + x + 1 (0x11b)",
    )


# ── GET /shamir/health ────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=ShamirHealthResponse,
    summary="Shamir engine self-test",
)
async def shamir_health():
    """
    Run a full split→reconstruct cycle with a test payload.
    Verifies the GF(2^8) arithmetic is functioning correctly.
    """
    try:
        import os, base64
        # Use 32 random bytes as test secret (simulates an AES-256 key)
        test_secret  = os.urandom(32)
        test_payload = base64.b64encode(test_secret).decode("utf-8")

        # Split into N=4 shares
        share_dicts  = split_encrypted_payload(test_payload)

        # Reconstruct from exactly K=3 shares (drop share index 3)
        k_shares     = share_dicts[:THRESHOLD]
        reconstructed = reconstruct_encrypted_payload(k_shares, len(test_secret))

        passed = reconstructed == test_payload

    except Exception:
        passed = False

    return ShamirHealthResponse(
        status="ok" if passed else "degraded",
        total_shares=TOTAL_SHARES,
        threshold=THRESHOLD,
        test_passed=passed,
    )