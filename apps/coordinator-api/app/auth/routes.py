from fastapi import APIRouter, Depends, HTTPException, status, Cookie, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, LogoutRequest
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
@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token = create_access_token({"sub": str(user.id)})

    refresh = await store_refresh_token(db, user.id)

    # 🔐 Store refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh.token,
        httponly=True,
        secure=False,  # set True in production (HTTPS)
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ---------------------------
# REFRESH TOKEN
# ---------------------------
@router.post("/refresh")
async def refresh_token(
    response: Response,
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    refresh = await validate_refresh_token(db, refresh_token)

    if not refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # 🔁 Rotate token
    await revoke_refresh_token(db, refresh_token)

    new_refresh = await store_refresh_token(db, refresh.user_id)
    new_access = create_access_token({"sub": str(refresh.user_id)})

    # Update cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh.token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return {
        "access_token": new_access,
        "token_type": "bearer"
    }

# ---------------------------
# LOGOUT
# ---------------------------
@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    if refresh_token:
        await revoke_refresh_token(db, refresh_token)

    # Delete cookie
    response.delete_cookie("refresh_token")

    return {
        "success": True,
        "message": "Logged out successfully"
    }
