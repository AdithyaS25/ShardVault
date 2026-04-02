"""
audit/routes.py — ShardLock Coordinator API
============================================
Audit log query endpoints. Implements §2.6 Audit and Logging System.

Registered in main.py as:
    from app.audit.routes import router as audit_router
    app.include_router(audit_router, prefix="/api/v1")

Endpoints:
    GET /api/v1/audit-logs          — all logs, paginated + filtered (admin only)
    GET /api/v1/audit-logs/me       — current user's own logs
    GET /api/v1/audit-logs/summary  — action count summary (admin only)

Auth:
    - /me        : any authenticated user
    - all others : admin role required

The write path (log_action) is NOT here — it lives in audit_service.py
and is called directly from every other module's endpoints.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_roles
from app.models.user import User
from app.services.audit_service import (
    get_audit_logs,
    get_my_audit_logs,
    get_audit_summary,
)
from app.schemas.audit import (
    AuditLogListResponse,
    AuditLogEntry,
    AuditLogSummaryResponse,
    ActionSummaryItem,
)

router = APIRouter(prefix="/audit-logs", tags=["Audit & Logging"])


# ── GET /audit-logs (admin only) ──────────────────────────────────────────────

@router.get(
    "",
    response_model=AuditLogListResponse,
    summary="List all audit logs — admin only",
)
async def list_audit_logs(
    user_id     : Optional[UUID]     = Query(None, description="Filter by user ID"),
    action      : Optional[str]      = Query(None, description="Filter by action e.g. LOGIN_FAILED"),
    from_date   : Optional[datetime] = Query(None, description="Logs from this datetime (ISO 8601)"),
    to_date     : Optional[datetime] = Query(None, description="Logs up to this datetime (ISO 8601)"),
    page        : int                = Query(default=1, ge=1),
    page_size   : int                = Query(default=50, ge=1, le=200),
    db          : AsyncSession       = Depends(get_db),
    current_user: User               = Depends(require_roles(["admin"])),
):
    """
    Admin-only. Returns all audit logs with optional filters.
    Supports filtering by user_id, action type, and date range.
    """
    logs, total = await get_audit_logs(
        db=db,
        user_id=user_id,
        action=action,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )

    return AuditLogListResponse(
        success=True,
        data=[AuditLogEntry.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── GET /audit-logs/me (any authenticated user) ───────────────────────────────

@router.get(
    "/me",
    response_model=AuditLogListResponse,
    summary="List current user's own audit logs",
)
async def list_my_audit_logs(
    action      : Optional[str]      = Query(None, description="Filter by action type"),
    from_date   : Optional[datetime] = Query(None, description="Logs from this datetime"),
    to_date     : Optional[datetime] = Query(None, description="Logs up to this datetime"),
    page        : int                = Query(default=1, ge=1),
    page_size   : int                = Query(default=20, ge=1, le=100),
    db          : AsyncSession       = Depends(get_db),
    current_user: User               = Depends(get_current_user),
):
    """
    Returns audit logs for the currently authenticated user only.
    Users cannot see other users' logs — enforced by filtering on user_id.
    """
    logs, total = await get_my_audit_logs(
        db=db,
        user_id=current_user.id,
        action=action,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )

    return AuditLogListResponse(
        success=True,
        data=[AuditLogEntry.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── GET /audit-logs/summary (admin only) ─────────────────────────────────────

@router.get(
    "/summary",
    response_model=AuditLogSummaryResponse,
    summary="Action count summary — admin only",
)
async def audit_summary(
    from_date   : Optional[datetime] = Query(None, description="From this datetime"),
    to_date     : Optional[datetime] = Query(None, description="Up to this datetime"),
    db          : AsyncSession       = Depends(get_db),
    current_user: User               = Depends(require_roles(["admin"])),
):
    """
    Admin-only. Returns count per action type across all users.
    Used by the admin monitoring dashboard (Module 8).

    Example response:
        LOGIN_SUCCESS    : 142
        VAULT_CREATED    : 87
        LOGIN_FAILED     : 23
        TOKEN_REFRESH_SUCCESS: 201
        ...
    """
    summary = await get_audit_summary(
        db=db,
        from_date=from_date,
        to_date=to_date,
    )

    return AuditLogSummaryResponse(
        success=True,
        data=[ActionSummaryItem(**item) for item in summary],
        from_date=from_date,
        to_date=to_date,
    )