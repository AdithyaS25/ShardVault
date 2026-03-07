"""
tests/unit/test_encryption.py — ShardLock
==========================================
Unit tests for the Encryption Engine (§2.2).
Covers: key derivation, encrypt, decrypt, IV uniqueness, tamper detection.

Run:
    pytest tests/unit/test_encryption.py -v
"""

import pytest
import base64

from app.crypto.encryption import (
    generate_salt,
    derive_encryption_key,
    encrypt_secret,
    decrypt_secret,
    payload_metadata,
    IV_SIZE_BYTES,
    TAG_SIZE_BYTES,
    KEY_SIZE_BYTES,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def salt():
    return generate_salt()

@pytest.fixture
def key(salt):
    return derive_encryption_key("test_master_password", salt)


# ── Salt ──────────────────────────────────────────────────────────────────────

class TestSalt:
    def test_salt_is_32_bytes(self):
        assert len(generate_salt()) == 32

    def test_salts_are_unique(self):
        assert generate_salt() != generate_salt()


# ── Key Derivation ────────────────────────────────────────────────────────────

class TestKeyDerivation:
    def test_key_is_32_bytes(self, salt):
        assert len(derive_encryption_key("password", salt)) == KEY_SIZE_BYTES

    def test_deterministic_same_inputs(self, salt):
        k1 = derive_encryption_key("password", salt)
        k2 = derive_encryption_key("password", salt)
        assert k1 == k2

    def test_different_passwords_different_keys(self, salt):
        assert derive_encryption_key("pass_A", salt) != derive_encryption_key("pass_B", salt)

    def test_different_salts_different_keys(self):
        s1, s2 = generate_salt(), generate_salt()
        assert derive_encryption_key("same", s1) != derive_encryption_key("same", s2)


# ── Encryption ────────────────────────────────────────────────────────────────

class TestEncrypt:
    def test_returns_string(self, key):
        assert isinstance(encrypt_secret("secret", key), str)

    def test_valid_base64(self, key):
        result = encrypt_secret("secret", key)
        decoded = base64.b64decode(result.encode())   # must not raise
        assert len(decoded) > 0

    def test_payload_minimum_length(self, key):
        raw = base64.b64decode(encrypt_secret("x", key).encode())
        assert len(raw) >= IV_SIZE_BYTES + TAG_SIZE_BYTES + 1

    def test_iv_unique_per_call(self, key):
        """Security critical — IV must never repeat."""
        p1 = base64.b64decode(encrypt_secret("same", key).encode())
        p2 = base64.b64decode(encrypt_secret("same", key).encode())
        assert p1[:IV_SIZE_BYTES] != p2[:IV_SIZE_BYTES]

    def test_probabilistic_encryption(self, key):
        """Same plaintext + same key must produce different ciphertexts."""
        assert encrypt_secret("hello", key) != encrypt_secret("hello", key)

    def test_wrong_key_length_raises(self):
        with pytest.raises(ValueError, match="Key must be"):
            encrypt_secret("test", b"tooshort")


# ── Decryption ────────────────────────────────────────────────────────────────

class TestDecrypt:
    def test_roundtrip_ascii(self, key):
        pt = "my-vault-password-123!@#"
        assert decrypt_secret(encrypt_secret(pt, key), key) == pt

    def test_roundtrip_unicode(self, key):
        pt = "пароль🔐漢字"
        assert decrypt_secret(encrypt_secret(pt, key), key) == pt

    def test_wrong_key_raises(self, salt):
        k1 = derive_encryption_key("pass_1", salt)
        k2 = derive_encryption_key("pass_2", salt)
        with pytest.raises(Exception):
            decrypt_secret(encrypt_secret("secret", k1), k2)

    def test_tampered_ciphertext_raises(self, key):
        """GCM authentication tag must catch any tampering."""
        raw = bytearray(base64.b64decode(encrypt_secret("secret", key).encode()))
        raw[-1] ^= 0xFF                               # flip last byte
        tampered = base64.b64encode(bytes(raw)).decode()
        with pytest.raises(Exception):
            decrypt_secret(tampered, key)

    def test_tampered_tag_raises(self, key):
        """Flip a byte in the tag region."""
        raw = bytearray(base64.b64decode(encrypt_secret("secret", key).encode()))
        raw[IV_SIZE_BYTES] ^= 0xFF                    # flip first tag byte
        tampered = base64.b64encode(bytes(raw)).decode()
        with pytest.raises(Exception):
            decrypt_secret(tampered, key)

    def test_invalid_base64_raises(self, key):
        with pytest.raises(ValueError, match="Invalid base64"):
            decrypt_secret("not!!valid!!base64###", key)

    def test_short_payload_raises(self, key):
        short = base64.b64encode(b"tooshort").decode()
        with pytest.raises(ValueError, match="Payload too short"):
            decrypt_secret(short, key)


# ── Metadata ──────────────────────────────────────────────────────────────────

class TestPayloadMetadata:
    def test_fields_present(self, key):
        meta = payload_metadata(encrypt_secret("hello", key))
        assert meta["algorithm"] == "AES-256-GCM"
        assert meta["iv_bytes"] == IV_SIZE_BYTES
        assert meta["tag_bytes"] == TAG_SIZE_BYTES
        assert meta["ciphertext_bytes"] >= 1