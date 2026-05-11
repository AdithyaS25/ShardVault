from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.refresh_token import RefreshToken
from app.core.security import create_refresh_token

REFRESH_EXPIRY_DAYS = 7


async def store_refresh_token(db: AsyncSession, user_id):
    token = create_refresh_token()

    refresh = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_EXPIRY_DAYS)
    )

    db.add(refresh)
    await db.flush()  # writes to DB within current transaction, no commit
    await db.refresh(refresh)  # safe to call after flush

    return refresh


async def revoke_refresh_token(db: AsyncSession, token: str):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == token)
    )
    refresh = result.scalar_one_or_none()

    if refresh:
        refresh.revoked = True
        # no commit — get_db commits on request exit


async def validate_refresh_token(db: AsyncSession, token: str):
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == token,
            RefreshToken.revoked == False
        )
    )

    refresh = result.scalar_one_or_none()

    if not refresh:
        return None

    if refresh.expires_at < datetime.utcnow():
        return None

    return refresh