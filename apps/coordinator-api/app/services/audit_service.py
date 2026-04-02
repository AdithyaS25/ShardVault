"""
services/audit_service.py — ShardLock Coordinator API
======================================================
DIFF from existing file:
  ADDED: query functions — get_audit_logs(), get_my_audit_logs(),
         get_audit_summary()
  UNCHANGED: log_action() — kept exactly as is, no modifications

The existing log_action() write path is already wired into every
endpoint across all modules. This file adds the read side.

Filters supported:
  - user_id   : filter by specific user (admin only)
  - action    : filter by action type (e.g. LOGIN_FAILED, VAULT_CREATED)
  - from_date : logs created after this datetime
  - to_date   : logs created before this datetime
  - page/page_size : pagination
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.audit_log import AuditLog


# ── Write (unchanged) ─────────────────────────────────────────────────────────

async def log_action(db: AsyncSession, user_id, action: str, ip: str = None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip,
    )
    db.add(log)
    await db.commit()


# ── Read — Admin: all logs with filters ───────────────────────────────────────

async def get_audit_logs(
    db          : AsyncSession,
    user_id     : Optional[UUID] = None,
    action      : Optional[str]  = None,
    from_date   : Optional[datetime] = None,
    to_date     : Optional[datetime] = None,
    page        : int = 1,
    page_size   : int = 50,
) -> tuple[list[AuditLog], int]:
    """
    Paginated audit log query with optional filters.
    Admin-only endpoint.

    Returns:
        (logs, total_count)
    """
    filters = []

    if user_id:
        filters.append(AuditLog.user_id == user_id)
    if action:
        filters.append(AuditLog.action == action)
    if from_date:
        filters.append(AuditLog.created_at >= from_date)
    if to_date:
        filters.append(AuditLog.created_at <= to_date)

    where_clause = and_(*filters) if filters else True

    # Total count
    count_result = await db.execute(
        select(func.count(AuditLog.id)).where(where_clause)
    )
    total = count_result.scalar_one()

    # Paginated results — newest first
    offset = (page - 1) * page_size
    result = await db.execute(
        select(AuditLog)
        .where(where_clause)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return list(logs), total


# ── Read — User: own logs only ────────────────────────────────────────────────

async def get_my_audit_logs(
    db          : AsyncSession,
    user_id     : UUID,
    action      : Optional[str] = None,
    from_date   : Optional[datetime] = None,
    to_date     : Optional[datetime] = None,
    page        : int = 1,
    page_size   : int = 20,
) -> tuple[list[AuditLog], int]:
    """
    Paginated audit logs for the authenticated user only.
    Regular users can only see their own logs.

    Returns:
        (logs, total_count)
    """
    filters = [AuditLog.user_id == user_id]

    if action:
        filters.append(AuditLog.action == action)
    if from_date:
        filters.append(AuditLog.created_at >= from_date)
    if to_date:
        filters.append(AuditLog.created_at <= to_date)

    where_clause = and_(*filters)

    count_result = await db.execute(
        select(func.count(AuditLog.id)).where(where_clause)
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(AuditLog)
        .where(where_clause)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return list(logs), total


# ── Read — Summary: action counts ────────────────────────────────────────────

async def get_audit_summary(
    db          : AsyncSession,
    from_date   : Optional[datetime] = None,
    to_date     : Optional[datetime] = None,
) -> list[dict]:
    """
    Returns count per action type across all users.
    Used by admin monitoring dashboard.

    Returns:
        [{"action": "LOGIN_SUCCESS", "count": 42}, ...]
    """
    filters = []
    if from_date:
        filters.append(AuditLog.created_at >= from_date)
    if to_date:
        filters.append(AuditLog.created_at <= to_date)

    where_clause = and_(*filters) if filters else True

    result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id).label("count"))
        .where(where_clause)
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
    )
    rows = result.all()

    return [{"action": row.action, "count": row.count} for row in rows]