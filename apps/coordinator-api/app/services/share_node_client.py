"""
services/share_node_client.py — ShardLock Coordinator API
===========================================================
HTTP client for coordinator → share node communication.

Implements §2.5 Inter-Service Communication requirements:
  - 3-second timeout per request
  - 2 retry attempts on failure
  - Fail reconstruction if threshold not met
  - All inter-service communication logged to audit_logs

Usage:
    client = ShareNodeClient(
        node_url="https://node-1.onrender.com",
        service_token=settings.INTERNAL_SERVICE_TOKEN,
        node_id="node-1",
    )
    await client.store_share(vault_entry_id, x_index, y_value)
    share = await client.retrieve_share(vault_entry_id)
    await client.delete_share(vault_entry_id)
"""

import asyncio
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# §2.5 Inter-service communication constants
REQUEST_TIMEOUT_SECONDS = 3
MAX_RETRIES             = 2
RETRY_DELAY_SECONDS     = 0.5


@dataclass
class ShareNodeConfig:
    """Configuration for a single share node."""
    node_id : str
    url     : str   # e.g. "https://shardlock-node-1.onrender.com"


class ShareNodeClient:
    """
    HTTP client for a single share node.
    Handles timeout, retry logic, and error logging per §2.5.
    """

    def __init__(self, config: ShareNodeConfig, service_token: str):
        self.config        = config
        self.service_token = service_token
        self._headers      = {
            "Authorization": f"Bearer {service_token}",
            "Content-Type" : "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """
        Execute an HTTP request with timeout and retry logic.

        Per §2.5:
          - Timeout: 3 seconds
          - Retries: 2 attempts
          - Logs all failures
        """
        url = f"{self.config.url}/internal/{path}"
        last_error = None

        for attempt in range(1, MAX_RETRIES + 2):  # attempts: 1, 2, 3
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                    response = await client.request(
                        method,
                        url,
                        headers=self._headers,
                        **kwargs,
                    )
                    response.raise_for_status()
                    return response.json()

            except httpx.TimeoutException as e:
                last_error = f"Timeout on attempt {attempt}"
                logger.warning(
                    "Share node %s timeout (attempt %d/%d): %s",
                    self.config.node_id, attempt, MAX_RETRIES + 1, path
                )

            except httpx.HTTPStatusError as e:
                # Don't retry on 4xx — these are deterministic failures
                logger.error(
                    "Share node %s HTTP %d: %s",
                    self.config.node_id, e.response.status_code, path
                )
                raise ShareNodeError(
                    node_id=self.config.node_id,
                    message=f"HTTP {e.response.status_code}: {e.response.text}",
                )

            except httpx.RequestError as e:
                last_error = str(e)
                logger.warning(
                    "Share node %s connection error (attempt %d/%d): %s",
                    self.config.node_id, attempt, MAX_RETRIES + 1, str(e)
                )

            # Wait before retry (skip wait on last attempt)
            if attempt <= MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS)

        # All attempts exhausted
        logger.error(
            "Share node %s unreachable after %d attempts: %s",
            self.config.node_id, MAX_RETRIES + 1, path
        )
        raise ShareNodeError(
            node_id=self.config.node_id,
            message=f"Unreachable after {MAX_RETRIES + 1} attempts. Last error: {last_error}",
        )

    # ── Public Methods ────────────────────────────────────────────────────────

    async def store_share(
        self,
        vault_entry_id: str,
        x_index: int,
        y_value: str,
    ) -> dict:
        """
        POST /internal/store-share
        Store one share on this node. Called during vault creation.
        """
        return await self._request(
            "POST",
            "store-share",
            json={
                "vault_entry_id": vault_entry_id,
                "x_index"       : x_index,
                "y_value"       : y_value,
            },
        )

    async def retrieve_share(self, vault_entry_id: str) -> dict:
        """
        GET /internal/retrieve-share/{vault_entry_id}
        Retrieve share from this node. Called during vault reconstruction.
        Returns dict with x_index and y_value.
        """
        return await self._request("GET", f"retrieve-share/{vault_entry_id}")

    async def delete_share(self, vault_entry_id: str) -> dict:
        """
        DELETE /internal/delete-share/{vault_entry_id}
        Delete share from this node. Called when vault entry is deleted.
        """
        return await self._request("DELETE", f"delete-share/{vault_entry_id}")

    async def health_check(self) -> bool:
        """Check if this node is reachable. Returns True/False."""
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.get(f"{self.config.url}/health")
                return response.status_code == 200
        except Exception:
            return False


# ── Error Types ───────────────────────────────────────────────────────────────

class ShareNodeError(Exception):
    """Raised when a share node request fails after all retries."""
    def __init__(self, node_id: str, message: str):
        self.node_id = node_id
        self.message = message
        super().__init__(f"[{node_id}] {message}")


class ThresholdNotMetError(Exception):
    """
    Raised when coordinator cannot reach K=3 nodes during reconstruction.
    Per §2.5: fail reconstruction if threshold not met.
    """
    def __init__(self, available: int, required: int):
        self.available = available
        self.required  = required
        super().__init__(
            f"Threshold not met: need {required} shares, only {available} nodes responded"
        )


# ── Orchestrator ──────────────────────────────────────────────────────────────

class ShareNodeOrchestrator:
    """
    Coordinates operations across all N=4 share nodes.

    Instantiated once at app startup using node URLs from config.
    Used by vault endpoints to distribute/collect shares.
    """

    def __init__(self, node_configs: list[ShareNodeConfig], service_token: str):
        self.clients = [
            ShareNodeClient(config, service_token)
            for config in node_configs
        ]
        self.threshold = 3   # K=3 per §2.3

    async def distribute_shares(
        self,
        vault_entry_id: str,
        shares: list[dict],
    ) -> list[str]:
        """
        Send each share to its corresponding node concurrently.

        Args:
            vault_entry_id : UUID of the vault entry
            shares         : List of N share dicts [{x, y}, ...] from Shamir split

        Returns:
            List of node_ids that successfully stored their share

        Raises:
            ShareNodeError: if any node fails to store (vault creation is all-or-nothing)
        """
        tasks = [
            client.store_share(
                vault_entry_id=vault_entry_id,
                x_index=shares[i]["x"],
                y_value=shares[i]["y"],
            )
            for i, client in enumerate(self.clients)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        failed = [
            self.clients[i].config.node_id
            for i, r in enumerate(results)
            if isinstance(r, Exception)
        ]

        if failed:
            # Attempt cleanup on successful nodes to avoid partial state
            await self._cleanup_shares(vault_entry_id, exclude_failed=failed)
            raise ShareNodeError(
                node_id=str(failed),
                message=f"Failed to store share on nodes: {failed}. Rolled back successful nodes.",
            )

        return [c.config.node_id for c in self.clients]

    async def collect_shares(self, vault_entry_id: str) -> list[dict]:
        """
        Retrieve shares from all nodes concurrently, return first K that respond.

        Per §2.5: fail reconstruction if threshold not met.

        Returns:
            List of K share dicts with x_index and y_value

        Raises:
            ThresholdNotMetError: if fewer than K=3 nodes respond
        """
        tasks = [
            client.retrieve_share(vault_entry_id)
            for client in self.clients
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful_shares = [
            {"x": r["x_index"], "y": r["y_value"]}
            for r in results
            if not isinstance(r, Exception)
        ]

        if len(successful_shares) < self.threshold:
            raise ThresholdNotMetError(
                available=len(successful_shares),
                required=self.threshold,
            )

        # Return exactly K shares — more than needed is fine but K is enough
        return successful_shares[:self.threshold]

    async def delete_shares(self, vault_entry_id: str) -> None:
        """
        Delete shares from all nodes concurrently.
        Called when a vault entry is deleted.
        Logs failures but does not raise — best-effort deletion.
        """
        tasks = [
            client.delete_share(vault_entry_id)
            for client in self.clients
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Failed to delete share from node %s for vault_entry %s: %s",
                    self.clients[i].config.node_id,
                    vault_entry_id,
                    str(result),
                )

    async def _cleanup_shares(
        self,
        vault_entry_id: str,
        exclude_failed: list[str],
    ) -> None:
        """Delete shares from nodes that succeeded, to roll back partial distribution."""
        tasks = [
            client.delete_share(vault_entry_id)
            for client in self.clients
            if client.config.node_id not in exclude_failed
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def node_health_status(self) -> list[dict]:
        """Check health of all nodes. Used by admin monitoring dashboard."""
        tasks = [client.health_check() for client in self.clients]
        results = await asyncio.gather(*tasks)
        return [
            {
                "node_id": self.clients[i].config.node_id,
                "url"    : self.clients[i].config.url,
                "online" : results[i],
            }
            for i in range(len(self.clients))
        ]