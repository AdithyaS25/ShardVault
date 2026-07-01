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
)
async def store_share(
    body: StoreShareRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_internal_token),
):
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
    await db.flush()
    await db.refresh(share)
    # no commit — get_db commits on exit

    return StoreShareResponse(
        success=True,
        vault_entry_id=body.vault_entry_id,
        node_id=settings.NODE_ID,
        message="Share stored successfully",
    )


@router.get(
    "/retrieve-share/{vault_entry_id}",
    response_model=RetrieveShareResponse,
)
async def retrieve_share(
    vault_entry_id: str,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_internal_token),
):
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


@router.delete(
    "/delete-share/{vault_entry_id}",
    response_model=DeleteShareResponse,
)
async def delete_share(
    vault_entry_id: str,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_internal_token),
):
    result = await db.execute(
        select(Share).where(Share.vault_entry_id == vault_entry_id)
    )
    share = result.scalar_one_or_none()

    if share:
        await db.delete(share)
        # no commit — get_db commits on exit
        message = "Share deleted successfully"
    else:
        message = "Share not found — nothing to delete"

    return DeleteShareResponse(
        success=True,
        vault_entry_id=vault_entry_id,
        node_id=settings.NODE_ID,
        message=message,
    )