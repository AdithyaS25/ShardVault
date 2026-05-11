import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

security = HTTPBearer()


def verify_internal_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> bool:
    """
    Verify the internal service token sent by the coordinator.

    Uses secrets.compare_digest to prevent timing attacks.
    Raises 403 (not 401) to avoid leaking that auth exists.
    """
    is_valid = secrets.compare_digest(
        credentials.credentials,
        settings.INTERNAL_SERVICE_TOKEN,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal service token",
        )

    return True