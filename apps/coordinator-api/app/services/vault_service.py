"""
services/vault_service.py — ShardLock Coordinator API
======================================================
Vault business logic — the integration layer that wires together:
  1. Encryption Engine   (app/crypto/encryption.py)
  2. Shamir SSS Engine   (app/shamir/shamir.py)
  3. Share Node Orchestrator (app/services/share_node_client.py)
  4. Database (vault_entries table)

This is the core of the ShardLock system per §2.9 sequence flows.

Vault Creation Flow:
  1. Derive AES key from master_password + user.encryption_salt
  2. Encrypt plaintext_password → encrypted_payload (AES-256-GCM)
  3. Split encrypted_payload → N=4 shares (Shamir GF(2^8))
  4. Distribute shares to 4 share nodes concurrently
  5. Store vault metadata (NOT the payload) in vault_entries table
  6. Audit log the creation

Vault Reconstruction Flow (GET /vault/{id}):
  1. Fetch vault metadata from DB
  2. Collect K=3 shares from share nodes concurrently
  3. Reconstruct encrypted_payload from shares (Shamir interpolation)
  4. Derive AES key from master_password + user.encryption_salt
  5. Decrypt encrypted_payload → plaintext_password
  6. Return plaintext — never stored anywhere

Vault Deletion Flow:
  1. Delete shares from all nodes concurrently (best-effort)
  2. Delete metadata from vault_entries table
  3. Audit log the deletion
"""

import base64
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.vault_entry import VaultEntry
from app.models.user import User
from app.crypto.encryption import derive_encryption_key, encrypt_secret, decrypt_secret
from app.shamir.shamir import split_encrypted_payload, reconstruct_encrypted_payload
from app.services.share_node_client import ShareNodeOrchestrator, ThresholdNotMetError, ShareNodeError

logger = logging.getLogger(__name__)


# ── Create ────────────────────────────────────────────────────────────────────

async def create_vault_entry(
    db              : AsyncSession,
    user            : User,
    site_name       : str,
    username        : str,
    plaintext_password: str,
    master_password : str,
    orchestrator    : ShareNodeOrchestrator,
    label           : str | None = None,
) -> VaultEntry:
    """
    Full vault creation flow per §2.9 vault creation sequence.

    Raises:
        ValueError      : if user has no encryption_salt
        ShareNodeError  : if any share node fails to store (rolled back automatically)
    """
    # ── Step 1: Validate user has encryption salt ─────────────────────────────
    if not user.encryption_salt:
        raise ValueError(
            "User has no encryption_salt. "
            "This should have been set at registration. "
            "Run a migration or re-register."
        )

    # ── Step 2: Derive AES key ────────────────────────────────────────────────
    # Key is derived on-the-fly and discarded — never stored (§2.2)
    aes_key = derive_encryption_key(master_password, user.encryption_salt)

    # ── Step 3: Encrypt the plaintext password ────────────────────────────────
    encrypted_payload = encrypt_secret(plaintext_password, aes_key)

    # ── Step 4: Calculate payload byte length for Shamir reconstruction ───────
    # reconstruct_secret() needs the exact byte length later
    payload_bytes = base64.b64decode(encrypted_payload.encode("utf-8"))
    payload_length = len(payload_bytes)

    # ── Step 5: Split into N=4 shares ─────────────────────────────────────────
    share_dicts = split_encrypted_payload(encrypted_payload)
    # Returns: [{"x": 1, "y": "base64..."}, {"x": 2, ...}, ...]

    # ── Step 6: Distribute shares to share nodes ──────────────────────────────
    # Create DB entry first to get the vault_entry_id for share node storage
    vault_entry = VaultEntry(
        user_id=user.id,
        site_name=site_name,
        username=username,
        label=label,
        encrypted_payload_length=payload_length,
    )
    db.add(vault_entry)
    await db.flush()   # Get the UUID without committing yet

    vault_id = str(vault_entry.id)

    try:
        await orchestrator.distribute_shares(
            vault_entry_id=vault_id,
            shares=share_dicts,
        )
    except (ShareNodeError, Exception) as e:
        # Roll back the DB flush — shares already rolled back by orchestrator
        await db.rollback()
        logger.error("Vault creation failed during share distribution: %s", str(e))
        raise

    # ── Step 7: Commit metadata to DB ─────────────────────────────────────────
    await db.commit()
    await db.refresh(vault_entry)

    logger.info("Vault entry %s created for user %s", vault_id, str(user.id))
    return vault_entry


# ── List ──────────────────────────────────────────────────────────────────────

async def list_vault_entries(
    db       : AsyncSession,
    user     : User,
    page     : int = 1,
    page_size: int = 20,
) -> tuple[list[VaultEntry], int]:
    """
    Return paginated vault metadata for a user.
    No passwords, no encrypted data — metadata only.

    Returns:
        (entries, total_count)
    """
    offset = (page - 1) * page_size

    # Total count
    count_result = await db.execute(
        select(func.count(VaultEntry.id)).where(VaultEntry.user_id == user.id)
    )
    total = count_result.scalar_one()

    # Paginated entries
    result = await db.execute(
        select(VaultEntry)
        .where(VaultEntry.user_id == user.id)
        .order_by(VaultEntry.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    entries = result.scalars().all()

    return list(entries), total


# ── Retrieve (reconstruct) ────────────────────────────────────────────────────

async def retrieve_vault_entry(
    db             : AsyncSession,
    user           : User,
    vault_entry_id : UUID,
    master_password: str,
    orchestrator   : ShareNodeOrchestrator,
) -> str:
    """
    Full vault reconstruction flow per §2.9 reconstruction sequence.

    Returns:
        plaintext_password string — caller must not store this

    Raises:
        ValueError         : vault not found or wrong user
        ThresholdNotMetError: fewer than K=3 share nodes responded
        cryptography.exceptions.InvalidTag: wrong master password
    """
    # ── Step 1: Fetch vault metadata ──────────────────────────────────────────
    result = await db.execute(
        select(VaultEntry).where(
            VaultEntry.id == vault_entry_id,
            VaultEntry.user_id == user.id,   # ownership check
        )
    )
    vault_entry = result.scalar_one_or_none()

    if not vault_entry:
        raise ValueError("Vault entry not found")

    # ── Step 2: Validate encryption salt ─────────────────────────────────────
    if not user.encryption_salt:
        raise ValueError("User has no encryption_salt")

    # ── Step 3: Collect K=3 shares from nodes ────────────────────────────────
    share_dicts = await orchestrator.collect_shares(str(vault_entry_id))
    # Returns: [{"x": int, "y": "base64..."}, ...] — at least K=3

    # ── Step 4: Reconstruct encrypted_payload ────────────────────────────────
    encrypted_payload = reconstruct_encrypted_payload(
        share_dicts=share_dicts,
        secret_length=vault_entry.encrypted_payload_length,
    )

    # ── Step 5: Derive AES key and decrypt ────────────────────────────────────
    aes_key = derive_encryption_key(master_password, user.encryption_salt)
    plaintext_password = decrypt_secret(encrypted_payload, aes_key)

    logger.info(
        "Vault entry %s reconstructed for user %s",
        str(vault_entry_id), str(user.id)
    )
    return plaintext_password


# ── Delete ────────────────────────────────────────────────────────────────────

async def delete_vault_entry(
    db             : AsyncSession,
    user           : User,
    vault_entry_id : UUID,
    orchestrator   : ShareNodeOrchestrator,
) -> None:
    """
    Delete vault entry — removes shares from all nodes then removes DB record.

    Per §2.9 deletion sequence:
      1. Delete shares from nodes (best-effort, logged on failure)
      2. Delete metadata from DB

    Raises:
        ValueError: vault not found or wrong user
    """
    # ── Step 1: Ownership check ───────────────────────────────────────────────
    result = await db.execute(
        select(VaultEntry).where(
            VaultEntry.id == vault_entry_id,
            VaultEntry.user_id == user.id,
        )
    )
    vault_entry = result.scalar_one_or_none()

    if not vault_entry:
        raise ValueError("Vault entry not found")

    # ── Step 2: Delete shares from nodes (best-effort) ────────────────────────
    await orchestrator.delete_shares(str(vault_entry_id))

    # ── Step 3: Delete metadata from DB ──────────────────────────────────────
    await db.delete(vault_entry)
    await db.commit()

    logger.info(
        "Vault entry %s deleted for user %s",
        str(vault_entry_id), str(user.id)
    )