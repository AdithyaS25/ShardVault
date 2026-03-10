"""
routes/shares.py — Share Node Service
=======================================
Internal API endpoints per §2.4 Share Node Internal API Specification.

All endpoints:
  - Require internal service token (coordinator-to-node auth)
  - Are prefixed /internal (set in main.py)
  - Are NOT accessible by end users

Endpoints:
  POST   /internal/store-share              — store a share for a vault entry
  GET    /internal/retrieve-share/{vault_entry_id} — retrieve share by vault entry
  DELETE /internal/delete-share/{vault_entry_id}   — delete share for vault entry
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import verify_internal_token
from app.models.share import Share
from app.schemas.share import (
    StoreShareRequest,
    StoreShareResponse,
    RetrieveShareResponse,
    DeleteShareResponse,
)

router = APIRouter(tags=["Internal Share Storage"])


# ── POST /internal/store-share ────────────────────────────────────────────────

@router.post(
    "/store-share",
    response_model=StoreShareResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store a secret share",
)
async def store_share(
    body: StoreShareRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_internal_token),
):
    """
    Store one Shamir share for a vault entry.

    Called by coordinator during vault creation flow:
      coordinator → POST /internal/store-share → this node

    Rejects duplicate vault_entry_id — each entry gets exactly one share
    per node. Coordinator must DELETE before re-storing (update flow).
    """
    # Check for existing share for this vault entry
    result = await db.execute(
        select(Share).where(Share.vault_entry_id == body.vault_entry_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Share for vault_entry_id '{body.vault_entry_id}' already exists on this node. DELETE first to update.",
        )

    share = Share(
        vault_entry_id=body.vault_entry_id,
        x_index=body.x_index,
        y_value=body.y_value,
    )

    db.add(share)
    await db.commit()
    await db.refresh(share)

    return StoreShareResponse(
        success=True,
        vault_entry_id=body.vault_entry_id,
        node_id=settings.NODE_ID,
        message="Share stored successfully",
    )


# ── GET /internal/retrieve-share/{vault_entry_id} ────────────────────────────

@router.get(
    "/retrieve-share/{vault_entry_id}",
    response_model=RetrieveShareResponse,
    summary="Retrieve a secret share",
)
async def retrieve_share(
    vault_entry_id: str,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_internal_token),
):
    """
    Retrieve the share for a given vault entry.

    Called by coordinator during vault reconstruction flow:
      coordinator → GET /internal/retrieve-share/{id} → this node

    Returns the (x_index, y_value) pair needed for Lagrange interpolation.
    Coordinator collects K=3 such responses from 3 different nodes.
    """
    result = await db.execute(
        select(Share).where(Share.vault_entry_id == vault_entry_id)
    )
    share = result.scalar_one_or_none()

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No share found for vault_entry_id '{vault_entry_id}' on node '{settings.NODE_ID}'",
        )

    return RetrieveShareResponse(
        vault_entry_id=share.vault_entry_id,
        x_index=share.x_index,
        y_value=share.y_value,
        node_id=settings.NODE_ID,
        created_at=share.created_at,
    )


# ── DELETE /internal/delete-share/{vault_entry_id} ───────────────────────────

@router.delete(
    "/delete-share/{vault_entry_id}",
    response_model=DeleteShareResponse,
    summary="Delete a secret share",
)
async def delete_share(
    vault_entry_id: str,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_internal_token),
):
    """
    Delete the share for a given vault entry.

    Called by coordinator when:
      - User deletes a vault entry (§1.5: DELETE vault removes metadata and shares)
      - Coordinator needs to re-store an updated share

    Returns success even if share didn't exist — idempotent delete.
    """
    result = await db.execute(
        select(Share).where(Share.vault_entry_id == vault_entry_id)
    )
    share = result.scalar_one_or_none()

    if share:
        await db.delete(share)
        await db.commit()
        message = "Share deleted successfully"
    else:
        message = "Share not found — nothing to delete"

    return DeleteShareResponse(
        success=True,
        vault_entry_id=vault_entry_id,
        node_id=settings.NODE_ID,
        message=message,
    )