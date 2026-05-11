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
    db                : AsyncSession,
    user              : User,
    site_name         : str,
    username          : str,
    plaintext_password: str,
    master_password   : str,
    orchestrator      : ShareNodeOrchestrator,
    label             : str | None = None,
) -> VaultEntry:
    if not user.encryption_salt:
        raise ValueError(
            "User has no encryption_salt. "
            "This should have been set at registration. "
            "Run a migration or re-register."
        )

    aes_key           = derive_encryption_key(master_password, user.encryption_salt)
    encrypted_payload = encrypt_secret(plaintext_password, aes_key)
    payload_bytes     = base64.b64decode(encrypted_payload.encode("utf-8"))
    payload_length    = len(payload_bytes)
    share_dicts       = split_encrypted_payload(encrypted_payload)

    vault_entry = VaultEntry(
        user_id=user.id,
        site_name=site_name,
        username=username,
        label=label,
        encrypted_payload_length=payload_length,
    )
    db.add(vault_entry)
    await db.flush()

    vault_id = str(vault_entry.id)

    try:
        await orchestrator.distribute_shares(
            vault_entry_id=vault_id,
            shares=share_dicts,
        )
    except (ShareNodeError, Exception) as e:
        logger.error("Vault creation failed during share distribution: %s", str(e))
        raise

    # no commit — get_db commits on exit
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
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count(VaultEntry.id)).where(VaultEntry.user_id == user.id)
    )
    total = count_result.scalar_one()

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
    result = await db.execute(
        select(VaultEntry).where(
            VaultEntry.id == vault_entry_id,
            VaultEntry.user_id == user.id,
        )
    )
    vault_entry = result.scalar_one_or_none()

    if not vault_entry:
        raise ValueError("Vault entry not found")

    if not user.encryption_salt:
        raise ValueError("User has no encryption_salt")

    share_dicts = await orchestrator.collect_shares(str(vault_entry_id))

    encrypted_payload = reconstruct_encrypted_payload(
        share_dicts=share_dicts,
        secret_length=vault_entry.encrypted_payload_length,
    )

    aes_key            = derive_encryption_key(master_password, user.encryption_salt)
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
    result = await db.execute(
        select(VaultEntry).where(
            VaultEntry.id == vault_entry_id,
            VaultEntry.user_id == user.id,
        )
    )
    vault_entry = result.scalar_one_or_none()

    if not vault_entry:
        raise ValueError("Vault entry not found")

    await orchestrator.delete_shares(str(vault_entry_id))

    await db.delete(vault_entry)
    # no commit — get_db commits on exit

    logger.info(
        "Vault entry %s deleted for user %s",
        str(vault_entry_id), str(user.id)
    )