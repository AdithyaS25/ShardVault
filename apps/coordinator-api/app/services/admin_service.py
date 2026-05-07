"""
services/admin_service.py — ShardLock Coordinator API
======================================================
Admin dashboard business logic.
"""

from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User
from app.models.vault_entry import VaultEntry
from app.models.audit_log import AuditLog


async def get_system_stats(db: AsyncSession) -> dict:
    total_users  = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_vaults = (await db.execute(select(func.count(VaultEntry.id)))).scalar_one()
    total_audits = (await db.execute(select(func.count(AuditLog.id)))).scalar_one()

    breakdown_result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id).label("count"))
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
    )
    audit_breakdown = {row.action: row.count for row in breakdown_result.all()}

    return {
        "total_users"         : total_users,
        "total_vault_entries" : total_vaults,
        "total_audit_events"  : total_audits,
        "audit_breakdown"     : audit_breakdown,
    }


async def get_all_users(
    db        : AsyncSession,
    page      : int = 1,
    page_size : int = 20,
) -> tuple[list[dict], int]:
    total = (await db.execute(select(func.count(User.id)))).scalar_one()
    offset = (page - 1) * page_size

    users_result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = users_result.scalars().all()

    vault_counts_result = await db.execute(
        select(VaultEntry.user_id, func.count(VaultEntry.id).label("count"))
        .group_by(VaultEntry.user_id)
    )
    vault_counts = {row.user_id: row.count for row in vault_counts_result.all()}

    return [
        {
            "id"         : u.id,
            "email"      : u.email,
            "role"       : u.role,
            "vault_count": vault_counts.get(u.id, 0),
            "created_at" : u.created_at,
        }
        for u in users
    ], total


async def get_user_detail(db: AsyncSession, user_id: UUID) -> Optional[dict]:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None

    vault_count = (
        await db.execute(
            select(func.count(VaultEntry.id)).where(VaultEntry.user_id == user_id)
        )
    ).scalar_one()

    recent_result = await db.execute(
        select(AuditLog.action)
        .where(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(5)
    )
    recent_actions = [row.action for row in recent_result.all()]

    return {
        "id"            : user.id,
        "email"         : user.email,
        "role"          : user.role,
        "vault_count"   : vault_count,
        "created_at"    : user.created_at,
        "recent_actions": recent_actions,
    }