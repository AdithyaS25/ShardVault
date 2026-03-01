from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


async def log_action(db: AsyncSession, user_id, action: str, ip: str = None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip
    )

    db.add(log)
    await db.commit()
    