from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.share_nodes import get_orchestrator
from app.models.user import User
from app.models.vault_entry import VaultEntry
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
    # ✅ FIX: Eagerly capture all fields from current_user BEFORE any try/except.
    # After a ShareNodeError triggers a DB ROLLBACK, SQLAlchemy expires all ORM
    # objects. Accessing current_user.id inside the except block then fires a
    # synchronous lazy reload outside the async greenlet context → MissingGreenlet.
    user_id = current_user.id
    client_ip = request.client.host

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

        await log_action(db, user_id=user_id, action="VAULT_CREATED", ip=client_ip)

        return VaultCreateResponse(
            success=True,
            message="Vault entry created and shares distributed",
            vault_id=str(vault_entry.id),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except ShareNodeError as e:
        # user_id is already captured above — safe to use after ROLLBACK
        await log_action(db, user_id=user_id, action="VAULT_CREATE_FAILED", ip=client_ip)
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
    vault_id       : UUID,
    master_password: str = Query(..., description="Master password to decrypt"),
    request        : Request = None,
    db             : AsyncSession = Depends(get_db),
    current_user   : User = Depends(get_current_user),
    orchestrator   : ShareNodeOrchestrator = Depends(get_orchestrator),
):
    # ✅ FIX: Same pattern — capture before try/except
    user_id = current_user.id
    client_ip = request.client.host if request else "unknown"

    try:
        plaintext = await retrieve_vault_entry(
            db=db,
            user=current_user,
            vault_entry_id=vault_id,
            master_password=master_password,
            orchestrator=orchestrator,
        )

        result = await db.execute(
            select(VaultEntry).where(VaultEntry.id == vault_id)
        )
        vault_entry = result.scalar_one()

        await log_action(db, user_id=user_id, action="VAULT_RETRIEVED", ip=client_ip)

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
        await log_action(db, user_id=user_id, action="VAULT_RECONSTRUCT_FAILED", ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Reconstruction failed: only {e.available}/{e.required} share nodes responded",
        )

    except Exception:
        await log_action(db, user_id=user_id, action="VAULT_DECRYPT_FAILED", ip=client_ip)
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
    # ✅ FIX: Same pattern
    user_id = current_user.id
    client_ip = request.client.host

    try:
        await delete_vault_entry(
            db=db,
            user=current_user,
            vault_entry_id=vault_id,
            orchestrator=orchestrator,
        )

        await log_action(db, user_id=user_id, action="VAULT_DELETED", ip=client_ip)

        return VaultDeleteResponse(
            success=True,
            message="Vault entry and all shares deleted",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))