"""
vault/routes.py — ShardLock Coordinator API
============================================
Vault management endpoints. Implements §1.5 Vault Interaction Flow.

Registered in main.py as:
    from app.vault.routes import router as vault_router
    app.include_router(vault_router, prefix="/api/v1")

Endpoints:
    POST   /api/v1/vault          — encrypt, split, distribute → create entry
    GET    /api/v1/vault          — paginated metadata list (no passwords)
    GET    /api/v1/vault/{id}     — reconstruct and return plaintext password
    DELETE /api/v1/vault/{id}     — delete shares + metadata

Auth: all endpoints require Bearer JWT (get_current_user dependency).
Master password: sent in request body, used only to derive AES key,
                 never logged or stored anywhere.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.share_nodes import get_orchestrator
from app.models.user import User
from app.services.share_node_client import ShareNodeOrchestrator, ThresholdNotMetError, ShareNodeError
from app.services.vault_service import (
    create_vault_entry,
    list_vault_entries,
    retrieve_vault_entry,
    delete_vault_entry,
)
from app.services.audit_service import log_action
from app.schemas.vault import (
    VaultCreateRequest,
    VaultCreateResponse,
    VaultListResponse,
    VaultEntryMeta,
    VaultRetrieveResponse,
    VaultDeleteResponse,
)

router = APIRouter(prefix="/vault", tags=["Vault Management"])


# ── POST /vault ───────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=VaultCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create vault entry — encrypt, split and distribute",
)
async def create_vault(
    payload     : VaultCreateRequest,
    request     : Request,
    db          : AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    orchestrator: ShareNodeOrchestrator = Depends(get_orchestrator),
):
    """
    Full vault creation flow:
      1. AES-256-GCM encrypt the plaintext password
      2. Shamir-split the encrypted payload into N=4 shares
      3. Distribute shares to 4 independent share nodes
      4. Store metadata (NOT the payload) in vault_entries
    """
    try:
        vault_entry = await create_vault_entry(
            db=db,
            user=current_user,
            site_name=payload.site_name,
            username=payload.username,
            plaintext_password=payload.plaintext_password,
            master_password=payload.master_password,
            orchestrator=orchestrator,
            label=payload.label,
        )

        await log_action(
            db,
            user_id=current_user.id,
            action="VAULT_CREATED",
            ip=request.client.host,
        )

        return VaultCreateResponse(
            success=True,
            message="Vault entry created and shares distributed",
            vault_id=str(vault_entry.id),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except ShareNodeError as e:
        await log_action(
            db,
            user_id=current_user.id,
            action="VAULT_CREATE_FAILED",
            ip=request.client.host,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Share distribution failed: {e.message}",
        )


# ── GET /vault ────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=VaultListResponse,
    summary="List vault entries — metadata only, paginated",
)
async def list_vaults(
    page        : int = Query(default=1, ge=1),
    page_size   : int = Query(default=20, ge=1, le=100),
    db          : AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns paginated vault metadata for the authenticated user.
    No passwords, no encrypted payloads — site names and usernames only.
    """
    entries, total = await list_vault_entries(
        db=db,
        user=current_user,
        page=page,
        page_size=page_size,
    )

    return VaultListResponse(
        success=True,
        data=[VaultEntryMeta.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── GET /vault/{vault_id} ─────────────────────────────────────────────────────

@router.get(
    "/{vault_id}",
    response_model=VaultRetrieveResponse,
    summary="Retrieve vault entry — triggers Shamir reconstruction",
)
async def get_vault(
    vault_id    : UUID,
    master_password: str = Query(..., description="Master password to decrypt"),
    request     : Request = None,
    db          : AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    orchestrator: ShareNodeOrchestrator = Depends(get_orchestrator),
):
    """
    Full reconstruction flow:
      1. Fetch vault metadata from DB
      2. Collect K=3 shares from share nodes
      3. Reconstruct encrypted_payload via Shamir interpolation
      4. Decrypt with AES-256-GCM using derived key
      5. Return plaintext — never stored

    master_password is sent as a query param here for simplicity.
    In production consider moving it to a POST body or header.
    """
    try:
        plaintext = await retrieve_vault_entry(
            db=db,
            user=current_user,
            vault_entry_id=vault_id,
            master_password=master_password,
            orchestrator=orchestrator,
        )

        # Fetch metadata for response
        from sqlalchemy import select
        from app.models.vault_entry import VaultEntry
        result = await db.execute(
            select(VaultEntry).where(VaultEntry.id == vault_id)
        )
        vault_entry = result.scalar_one()

        await log_action(
            db,
            user_id=current_user.id,
            action="VAULT_RETRIEVED",
            ip=request.client.host if request else "unknown",
        )

        return VaultRetrieveResponse(
            success=True,
            vault_id=str(vault_id),
            site_name=vault_entry.site_name,
            username=vault_entry.username,
            label=vault_entry.label,
            plaintext_password=plaintext,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except ThresholdNotMetError as e:
        await log_action(
            db,
            user_id=current_user.id,
            action="VAULT_RECONSTRUCT_FAILED",
            ip=request.client.host if request else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Reconstruction failed: only {e.available}/{e.required} share nodes responded",
        )

    except Exception:
        # Covers InvalidTag (wrong master password) and other crypto errors
        await log_action(
            db,
            user_id=current_user.id,
            action="VAULT_DECRYPT_FAILED",
            ip=request.client.host if request else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Decryption failed: invalid master password or tampered data",
        )


# ── DELETE /vault/{vault_id} ──────────────────────────────────────────────────

@router.delete(
    "/{vault_id}",
    response_model=VaultDeleteResponse,
    summary="Delete vault entry — removes shares and metadata",
)
async def delete_vault(
    vault_id    : UUID,
    request     : Request,
    db          : AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    orchestrator: ShareNodeOrchestrator = Depends(get_orchestrator),
):
    """
    Deletion flow:
      1. Best-effort delete shares from all N=4 nodes
      2. Delete metadata from vault_entries table
    Node failures are logged but do not block DB deletion.
    """
    try:
        await delete_vault_entry(
            db=db,
            user=current_user,
            vault_entry_id=vault_id,
            orchestrator=orchestrator,
        )

        await log_action(
            db,
            user_id=current_user.id,
            action="VAULT_DELETED",
            ip=request.client.host,
        )

        return VaultDeleteResponse(
            success=True,
            message="Vault entry and all shares deleted",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))