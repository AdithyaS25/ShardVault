"""
schemas/admin.py — ShardLock Coordinator API
=============================================
Pydantic schemas for admin monitoring dashboard endpoints.
"""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel


class AdminStatsResponse(BaseModel):
    success             : bool
    total_users         : int
    total_vault_entries : int
    total_audit_events  : int
    audit_breakdown     : dict


class AdminUserItem(BaseModel):
    id          : UUID
    email       : str
    role        : str
    vault_count : int
    created_at  : datetime

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    success   : bool
    data      : List[AdminUserItem]
    total     : int
    page      : int
    page_size : int


class AdminUserDetailResponse(BaseModel):
    success        : bool
    id             : UUID
    email          : str
    role           : str
    vault_count    : int
    created_at     : datetime
    recent_actions : List[str]


class NodeHealthItem(BaseModel):
    node_id : str
    url     : str
    online  : bool


class NodeHealthResponse(BaseModel):
    success       : bool
    nodes         : List[NodeHealthItem]
    online_count  : int
    offline_count : int
    threshold_met : bool