from fastapi import APIRouter, Depends, HTTPException, status, Cookie, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db, get_current_user, require_roles
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    RegisterResponse,
    LogoutResponse,
)
from app.core.security import hash_password, verify_password, create_access_token
from app.auth.refresh_service import (
    store_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
)
from app.services.audit_service import log_action
from app.crypto.encryption import generate_salt

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# ── Register ──────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="user",
        encryption_salt=generate_salt(),
    )

    db.add(new_user)
    # get_db commits on exit

    return RegisterResponse(success=True, message="User registered successfully")


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        await log_action(db, user_id=None, action="LOGIN_FAILED", ip=request.client.host)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh = await store_refresh_token(db, user.id)

    response.set_cookie(
        key="refresh_token",
        value=refresh.token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    await log_action(db, user_id=user.id, action="LOGIN_SUCCESS", ip=request.client.host)
    # get_db commits everything (refresh token + audit log) together on exit

    return LoginResponse(access_token=access_token)


# ── Refresh Token ─────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        await log_action(db, user_id=None, action="TOKEN_REFRESH_FAILED", ip=request.client.host)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    refresh = await validate_refresh_token(db, refresh_token)

    if not refresh:
        await log_action(db, user_id=None, action="TOKEN_REFRESH_FAILED", ip=request.client.host)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    await revoke_refresh_token(db, refresh_token)
    new_refresh = await store_refresh_token(db, refresh.user_id)
    new_access  = create_access_token({"sub": str(refresh.user_id)})

    response.set_cookie(
        key="refresh_token",
        value=new_refresh.token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    await log_action(db, user_id=refresh.user_id, action="TOKEN_REFRESH_SUCCESS", ip=request.client.host)

    return LoginResponse(access_token=new_access)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    user_id = None

    if refresh_token:
        refresh = await validate_refresh_token(db, refresh_token)
        if refresh:
            user_id = refresh.user_id
        await revoke_refresh_token(db, refresh_token)

    response.delete_cookie("refresh_token")

    await log_action(db, user_id=user_id, action="LOGOUT", ip=request.client.host)

    return LogoutResponse(success=True, message="Logged out successfully")


# ── Me (protected) ────────────────────────────────────────────────────────────

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id"   : str(current_user.id),
        "email": current_user.email,
        "role" : current_user.role,
    }


# ── Admin Only ────────────────────────────────────────────────────────────────

@router.get("/admin-only")
async def admin_only(current_user: User = Depends(require_roles(["admin"]))):
    return {"message": f"Welcome Admin — {current_user.email}"}


# ── Create Admin ──────────────────────────────────────────────────────────────

@router.post("/create-admin", status_code=status.HTTP_201_CREATED)
async def create_admin(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    admin_user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="admin",
        encryption_salt=generate_salt(),
    )

    db.add(admin_user)

    return {"message": f"Admin {payload.email} created successfully"}