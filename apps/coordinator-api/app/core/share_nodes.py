"""
core/share_nodes.py — ShardLock Coordinator API
=================================================
Wires share node URLs from .env into the ShareNodeOrchestrator.

Add these to coordinator's .env:
  INTERNAL_SERVICE_TOKEN=your-secret-token-here
  SHARE_NODE_1_URL=https://shardlock-node-1.onrender.com
  SHARE_NODE_2_URL=https://shardlock-node-2.onrender.com
  SHARE_NODE_3_URL=https://shardlock-node-3.onrender.com
  SHARE_NODE_4_URL=https://shardlock-node-4.onrender.com

For local dev, run 4 share node instances on different ports:
  SHARE_NODE_1_URL=http://localhost:8001
  SHARE_NODE_2_URL=http://localhost:8002
  SHARE_NODE_3_URL=http://localhost:8003
  SHARE_NODE_4_URL=http://localhost:8004
"""

from app.core.config import settings
from app.services.share_node_client import ShareNodeOrchestrator, ShareNodeConfig


def get_orchestrator() -> ShareNodeOrchestrator:
    """
    FastAPI dependency — returns the share node orchestrator.

    Usage in vault endpoints:
        @router.post("/vault")
        async def create_vault(
            orchestrator: ShareNodeOrchestrator = Depends(get_orchestrator),
        ):
    """
    node_configs = [
        ShareNodeConfig(node_id="node-1", url=settings.SHARE_NODE_1_URL),
        ShareNodeConfig(node_id="node-2", url=settings.SHARE_NODE_2_URL),
        ShareNodeConfig(node_id="node-3", url=settings.SHARE_NODE_3_URL),
        ShareNodeConfig(node_id="node-4", url=settings.SHARE_NODE_4_URL),
    ]

    return ShareNodeOrchestrator(
        node_configs=node_configs,
        service_token=settings.INTERNAL_SERVICE_TOKEN,
    )