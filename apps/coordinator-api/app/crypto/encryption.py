"""
encryption.py — ShardLock Coordinator API
==========================================
Core AES-256-GCM authenticated encryption engine.
Implements §2.2 Encryption Engine Design from ShardLock documentation.

Design rules enforced here:
  - AES-256-GCM: confidentiality + integrity in one pass
  - Unique 12-byte IV generated per encryption call (NEVER reused)
  - 16-byte authentication tag stored with ciphertext
  - Per-user key derived via Argon2id (PBKDF2-SHA256 fallback)
  - Master keys NEVER stored — derived on-the-fly, discarded after use

Payload wire format:
  base64( iv[12 bytes] | tag[16 bytes] | ciphertext[n bytes] )
"""

import os
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

try:
    from argon2.low_level import hash_secret_raw, Type
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False

# ── Constants ─────────────────────────────────────────────────────────────────
IV_SIZE_BYTES      = 12       # GCM standard nonce
TAG_SIZE_BYTES     = 16       # GCM authentication tag
KEY_SIZE_BYTES     = 32       # AES-256

# Argon2id params (OWASP 2023)
ARGON2_TIME_COST   = 2
ARGON2_MEMORY_COST = 65536    # 64 MB
ARGON2_PARALLELISM = 2
ARGON2_HASH_LEN    = 32

# PBKDF2 fallback params (OWASP 2023)
PBKDF2_ITERATIONS  = 600_000


# ── Salt ──────────────────────────────────────────────────────────────────────

def generate_salt() -> bytes:
    """
    Generate a cryptographically secure 32-byte random salt.
    Called once at user registration — stored in users table.
    """
    return os.urandom(32)


# ── Key Derivation ────────────────────────────────────────────────────────────

def derive_encryption_key(master_password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit AES key from the user's master password.

    Uses Argon2id (preferred) with PBKDF2-SHA256 as fallback.
    The derived key is NEVER stored anywhere — caller must discard after use.

    Args:
        master_password : User's plaintext master password
        salt            : Per-user random salt from users table

    Returns:
        32-byte encryption key
    """
    password_bytes = master_password.encode("utf-8")

    if ARGON2_AVAILABLE:
        key = hash_secret_raw(
            secret=password_bytes,
            salt=salt,
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN,
            type=Type.ID,
        )
    else:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE_BYTES,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        key = kdf.derive(password_bytes)

    return key


# ── Encrypt ───────────────────────────────────────────────────────────────────

def encrypt_secret(plaintext: str, key: bytes) -> str:
    """
    Encrypt a plaintext secret using AES-256-GCM.

    A fresh random IV is generated on every call — this is critical.
    The same plaintext encrypted twice will produce different ciphertexts.

    Args:
        plaintext : The secret/password to protect
        key       : 32-byte AES-256 key from derive_encryption_key()

    Returns:
        Base64-encoded string: iv | tag | ciphertext

    Raises:
        ValueError: if key length is not 32 bytes
    """
    if len(key) != KEY_SIZE_BYTES:
        raise ValueError(f"Key must be {KEY_SIZE_BYTES} bytes, got {len(key)}")

    iv = os.urandom(IV_SIZE_BYTES)          # Fresh IV every call — never reuse
    aesgcm = AESGCM(key)

    # encrypt() returns ciphertext with tag appended at the end
    ct_with_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)

    ciphertext = ct_with_tag[:-TAG_SIZE_BYTES]
    tag        = ct_with_tag[-TAG_SIZE_BYTES:]

    payload = iv + tag + ciphertext
    return base64.b64encode(payload).decode("utf-8")


# ── Decrypt ───────────────────────────────────────────────────────────────────

def decrypt_secret(encrypted_payload: str, key: bytes) -> str:
    """
    Decrypt an AES-256-GCM payload produced by encrypt_secret().

    The authentication tag is verified before any plaintext is returned.
    Raises InvalidTag if the payload was tampered with or the key is wrong.

    Args:
        encrypted_payload : Base64 string from encrypt_secret()
        key               : 32-byte AES-256 key (must match encryption key)

    Returns:
        Original plaintext string

    Raises:
        ValueError                        : malformed payload or bad base64
        cryptography.exceptions.InvalidTag: tampered data or wrong key
    """
    if len(key) != KEY_SIZE_BYTES:
        raise ValueError(f"Key must be {KEY_SIZE_BYTES} bytes, got {len(key)}")

    try:
        payload = base64.b64decode(encrypted_payload.encode("utf-8"))
    except Exception:
        raise ValueError("Invalid base64 payload")

    min_len = IV_SIZE_BYTES + TAG_SIZE_BYTES + 1
    if len(payload) < min_len:
        raise ValueError(f"Payload too short: minimum {min_len} bytes required")

    iv         = payload[:IV_SIZE_BYTES]
    tag        = payload[IV_SIZE_BYTES : IV_SIZE_BYTES + TAG_SIZE_BYTES]
    ciphertext = payload[IV_SIZE_BYTES + TAG_SIZE_BYTES :]

    aesgcm = AESGCM(key)
    plaintext_bytes = aesgcm.decrypt(iv, ciphertext + tag, None)
    return plaintext_bytes.decode("utf-8")


# ── Metadata (no decryption) ──────────────────────────────────────────────────

def payload_metadata(encrypted_payload: str) -> dict:
    """Return structural metadata about a payload without decrypting it."""
    raw = base64.b64decode(encrypted_payload.encode("utf-8"))
    return {
        "algorithm"        : "AES-256-GCM",
        "total_bytes"      : len(raw),
        "iv_bytes"         : IV_SIZE_BYTES,
        "tag_bytes"        : TAG_SIZE_BYTES,
        "ciphertext_bytes" : len(raw) - IV_SIZE_BYTES - TAG_SIZE_BYTES,
    }