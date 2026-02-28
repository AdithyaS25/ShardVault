from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.auth.refresh_service import (
    store_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# ---------------------------
# DB Dependency
# ---------------------------
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------
# REGISTER
# ---------------------------
@router.post("/register")
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = User(
        email=payload.email,
        password_hash=hash_password(payload.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "success": True,
        "message": "User registered successfully"
    }


# ---------------------------
# LOGIN
# ---------------------------
@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create access token
    access_token = create_access_token({"sub": str(user.id)})

    # Store refresh token in DB
    refresh = await store_refresh_token(db, user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh.token,
        "token_type": "bearer"
    }


# ---------------------------
# REFRESH TOKEN
# ---------------------------
@router.post("/refresh")
async def refresh_token(payload: dict, db: AsyncSession = Depends(get_db)):
    token = payload.get("refresh_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required"
        )

    refresh = await validate_refresh_token(db, token)

    if not refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # TOKEN ROTATION
    await revoke_refresh_token(db, token)

    new_refresh = await store_refresh_token(db, refresh.user_id)
    new_access = create_access_token({"sub": str(refresh.user_id)})

    return {
        "success": True,
        "data": {
            "access_token": new_access,
            "refresh_token": new_refresh.token,
            "token_type": "bearer"
        },
        "message": "Token refreshed successfully"
    }


# ---------------------------
# LOGOUT
# ---------------------------
@router.post("/logout")
async def logout(payload: dict, db: AsyncSession = Depends(get_db)):
    token = payload.get("refresh_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required"
        )

    await revoke_refresh_token(db, token)

    return {
        "success": True,
        "message": "Logged out successfully"
    }
