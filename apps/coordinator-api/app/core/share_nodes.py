"""
core/share_nodes.py — Coordinator Share Node Wiring
Temporary debug version.
"""

from app.core.config import settings
from app.services.share_node_client import (
    ShareNodeOrchestrator,
    ShareNodeConfig,
)


def get_orchestrator() -> ShareNodeOrchestrator:
    """
    Creates the ShareNodeOrchestrator and prints the loaded configuration.

    TEMP DEBUG:
    Remove the print statements after verification.
    """

    print("\n" + "=" * 70)
    print("SHARDVAULT SHARE NODE CONFIGURATION")
    print("=" * 70)
    print(f"NODE 1 : {settings.SHARE_NODE_1_URL}")
    print(f"NODE 2 : {settings.SHARE_NODE_2_URL}")
    print(f"NODE 3 : {settings.SHARE_NODE_3_URL}")
    print(f"NODE 4 : {settings.SHARE_NODE_4_URL}")
    print(f"TOKEN  : {settings.INTERNAL_SERVICE_TOKEN[:12]}...")
    print("=" * 70 + "\n")

    node_configs = [
        ShareNodeConfig(
            node_id="node-1",
            url=settings.SHARE_NODE_1_URL,
        ),
        ShareNodeConfig(
            node_id="node-2",
            url=settings.SHARE_NODE_2_URL,
        ),
        ShareNodeConfig(
            node_id="node-3",
            url=settings.SHARE_NODE_3_URL,
        ),
        ShareNodeConfig(
            node_id="node-4",
            url=settings.SHARE_NODE_4_URL,
        ),
    ]

    return ShareNodeOrchestrator(
        node_configs=node_configs,
        service_token=settings.INTERNAL_SERVICE_TOKEN,
    )