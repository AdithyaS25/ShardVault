"""
schemas/audit.py — ShardLock Coordinator API
=============================================
Pydantic schemas for audit logging endpoints.
Mirrors the pattern in schemas/auth.py and schemas/vault.py.

Endpoints served:
    GET /api/v1/audit-logs          — paginated audit log list (admin only)
    GET /api/v1/audit-logs/me       — current user's own audit logs
    GET /api/v1/audit-logs/summary  — action counts summary (admin only)
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


# ── Single Log Entry ──────────────────────────────────────────────────────────

class AuditLogEntry(BaseModel):
    id          : UUID
    user_id     : Optional[UUID]
    action      : str
    ip_address  : Optional[str]
    created_at  : datetime

    class Config:
        from_attributes = True


# ── List Response ─────────────────────────────────────────────────────────────

class AuditLogListResponse(BaseModel):
    success     : bool
    data        : List[AuditLogEntry]
    total       : int
    page        : int
    page_size   : int


# ── Summary Response ──────────────────────────────────────────────────────────

class ActionSummaryItem(BaseModel):
    action      : str
    count       : int


class AuditLogSummaryResponse(BaseModel):
    success     : bool
    data        : List[ActionSummaryItem]
    from_date   : Optional[datetime]
    to_date     : Optional[datetime]

