"""
admin/routes.py — ShardLock Coordinator API
============================================
Admin monitoring dashboard endpoints. Implements §2.7 Admin Dashboard.

Registered in main.py as:
    from app.admin.routes import router as admin_router
    app.include_router(admin_router, prefix="/api/v1")

Endpoints:
    GET /api/v1/admin/stats          — system-wide counts + audit breakdown
    GET /api/v1/admin/users          — paginated user list with vault counts
    GET /api/v1/admin/users/{id}     — single user detail + recent activity
    GET /api/v1/admin/nodes/health   — live health check of all 4 share nodes

All endpoints: admin role required.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.core.share_nodes import get_orchestrator
from app.models.user import User
from app.services.share_node_client import ShareNodeOrchestrator
from app.services.admin_service import (
    get_system_stats,
    get_all_users,
    get_user_detail,
)
from app.schemas.admin import (
    AdminStatsResponse,
    AdminUserItem,
    AdminUserListResponse,
    AdminUserDetailResponse,
    NodeHealthItem,
    NodeHealthResponse,
)

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


# ── GET /admin/stats ──────────────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="System-wide stats — admin only",
)
async def admin_stats(
    db          : AsyncSession = Depends(get_db),
    current_user: User         = Depends(require_roles(["admin"])),
):
    """
    Returns total users, vault entries, audit events, and
    a per-action breakdown. Used for the dashboard stats cards.
    """
    stats = await get_system_stats(db)
    return AdminStatsResponse(success=True, **stats)


# ── GET /admin/users ──────────────────────────────────────────────────────────

@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="All users with vault counts — admin only",
)
async def admin_list_users(
    page        : int          = Query(default=1, ge=1),
    page_size   : int          = Query(default=20, ge=1, le=100),
    db          : AsyncSession = Depends(get_db),
    current_user: User         = Depends(require_roles(["admin"])),
):
    """
    Paginated list of all registered users including their vault entry count.
    """
    users, total = await get_all_users(db=db, page=page, page_size=page_size)
    return AdminUserListResponse(
        success=True,
        data=[AdminUserItem(**u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── GET /admin/users/{user_id} ────────────────────────────────────────────────

@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetailResponse,
    summary="Single user detail — admin only",
)
async def admin_user_detail(
    user_id     : UUID,
    db          : AsyncSession = Depends(get_db),
    current_user: User         = Depends(require_roles(["admin"])),
):
    """
    Returns a single user's profile, vault count, and their
    last 5 audit actions.
    """
    detail = await get_user_detail(db=db, user_id=user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="User not found")

    return AdminUserDetailResponse(success=True, **detail)


# ── GET /admin/nodes/health ───────────────────────────────────────────────────

@router.get(
    "/nodes/health",
    response_model=NodeHealthResponse,
    summary="Live share node health — admin only",
)
async def admin_nodes_health(
    current_user: User                  = Depends(require_roles(["admin"])),
    orchestrator: ShareNodeOrchestrator = Depends(get_orchestrator),
):
    """
    Performs live health checks against all 4 share nodes concurrently.
    Returns online/offline status per node and whether K=3 threshold is met.

    This is the most visually impactful endpoint for the demo —
    shows 4 distinct node URLs and their live status.
    """
    node_statuses = await orchestrator.node_health_status()

    online_count  = sum(1 for n in node_statuses if n["online"])
    offline_count = len(node_statuses) - online_count

    return NodeHealthResponse(
        success=True,
        nodes=[NodeHealthItem(**n) for n in node_statuses],
        online_count=online_count,
        offline_count=offline_count,
        threshold_met=online_count >= 3,
    )