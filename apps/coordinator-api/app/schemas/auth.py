"""
schemas/auth.py — ShardLock Coordinator API
============================================
FIX APPLIED:
  - TokenResponse had a `refresh_token` field but the login endpoint
    sends the refresh token via HttpOnly cookie, NOT in the JSON body.
    Having it in the schema was misleading and would cause frontend
    developers to look for it in the wrong place.

  - Removed `refresh_token` from TokenResponse.
  - Added LoginResponse as the correct schema for the login endpoint.
  - Kept RefreshRequest and LogoutRequest even though routes use Cookie()
    directly — useful for documentation clarity.
"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    class Config:
        json_schema_extra = {
            "example": {"email": "user@example.com", "password": "securepass123"}
        }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {"email": "user@example.com", "password": "securepass123"}
        }


class LoginResponse(BaseModel):
    """
    Response for POST /auth/login and POST /auth/refresh.
    Refresh token is delivered via HttpOnly cookie — NOT in this body.
    """
    access_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    success: bool
    message: str


class LogoutResponse(BaseModel):
    success: bool
    message: str


# Kept for schema documentation — actual routes read cookie directly
class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str