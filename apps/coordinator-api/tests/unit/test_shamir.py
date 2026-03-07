"""
tests/unit/test_shamir.py — ShardLock
======================================
Unit tests for the Shamir Secret Sharing Engine (§2.3).

Covers:
  - GF(2^8) arithmetic correctness
  - Split produces correct number/structure of shares
  - Reconstruct with exactly K shares succeeds
  - Reconstruct with K+1, K+2 shares succeeds
  - Reconstruct with K-1 shares fails (threshold enforcement)
  - Wrong shares produce wrong output (information-theoretic check)
  - Full roundtrip with encrypted payload strings
  - Edge cases: single byte, large payloads, all share combinations

Run:
    pytest tests/unit/test_shamir.py -v
"""

import base64
import os
import itertools
import pytest

from app.shamir.shamir import (
    _gf_add,
    _gf_mul,
    _gf_inv,
    _gf_div,
    _evaluate_polynomial,
    _make_polynomial,
    _lagrange_interpolate_at_zero,
    split_secret,
    reconstruct_secret,
    split_encrypted_payload,
    reconstruct_encrypted_payload,
    encode_share,
    decode_share,
    TOTAL_SHARES,
    THRESHOLD,
)


# ── GF(2^8) Arithmetic ────────────────────────────────────────────────────────

class TestGF256Arithmetic:

    def test_add_is_xor(self):
        assert _gf_add(0b10101010, 0b11001100) == (0b10101010 ^ 0b11001100)

    def test_add_identity(self):
        """a + 0 = a in GF(2^8)"""
        for a in [0, 1, 127, 255]:
            assert _gf_add(a, 0) == a

    def test_add_self_is_zero(self):
        """a + a = 0 in GF(2^8) — characteristic 2"""
        for a in [1, 42, 128, 255]:
            assert _gf_add(a, a) == 0

    def test_mul_identity(self):
        """a * 1 = a"""
        for a in [1, 2, 127, 255]:
            assert _gf_mul(a, 1) == a

    def test_mul_zero(self):
        """a * 0 = 0"""
        for a in [0, 1, 128, 255]:
            assert _gf_mul(a, 0) == 0

    def test_mul_commutative(self):
        assert _gf_mul(53, 131) == _gf_mul(131, 53)

    def test_mul_result_in_field(self):
        """Result must always be a valid field element (0-255)"""
        for a in [0, 1, 127, 128, 255]:
            for b in [0, 1, 127, 128, 255]:
                result = _gf_mul(a, b)
                assert 0 <= result <= 255

    def test_distributive_law(self):
        """a * (b + c) = a*b + a*c"""
        a, b, c = 17, 89, 200
        assert _gf_mul(a, _gf_add(b, c)) == _gf_add(_gf_mul(a, b), _gf_mul(a, c))

    def test_inverse_correctness(self):
        """a * a^(-1) = 1 for all non-zero a"""
        for a in [1, 2, 7, 16, 127, 128, 200, 255]:
            assert _gf_mul(a, _gf_inv(a)) == 1

    def test_inverse_zero_raises(self):
        with pytest.raises(ValueError, match="Zero has no multiplicative inverse"):
            _gf_inv(0)

    def test_division(self):
        """a / b * b = a"""
        for a, b in [(10, 5), (255, 3), (128, 7), (1, 255)]:
            assert _gf_mul(_gf_div(a, b), b) == a


# ── Polynomial ────────────────────────────────────────────────────────────────

class TestPolynomial:

    def test_constant_term_is_secret(self):
        """f(0) must equal the secret byte."""
        for secret in [0, 1, 42, 128, 255]:
            poly = _make_polynomial(secret, degree=2)
            assert poly[0] == secret

    def test_degree_matches(self):
        poly = _make_polynomial(42, degree=2)
        assert len(poly) == 3   # degree 2 → 3 coefficients

    def test_evaluate_at_zero_returns_secret(self):
        for secret in [0, 99, 255]:
            poly = _make_polynomial(secret, degree=2)
            assert _evaluate_polynomial(poly, 0) == secret

    def test_evaluate_in_field(self):
        poly = _make_polynomial(42, degree=2)
        for x in range(1, 10):
            result = _evaluate_polynomial(poly, x)
            assert 0 <= result <= 255


# ── Split ─────────────────────────────────────────────────────────────────────

class TestSplit:

    def test_returns_n_shares(self):
        secret = os.urandom(16)
        shares = split_secret(secret)
        assert len(shares) == TOTAL_SHARES

    def test_share_x_indices(self):
        """x-indices must be 1..N (never 0 — that's the secret)"""
        shares = split_secret(os.urandom(8))
        x_vals = [s[0] for s in shares]
        assert sorted(x_vals) == list(range(1, TOTAL_SHARES + 1))

    def test_share_y_length_matches_secret(self):
        for length in [1, 16, 32, 64]:
            secret = os.urandom(length)
            shares = split_secret(secret)
            for _, y in shares:
                assert len(y) == length

    def test_shares_are_distinct(self):
        """Each share's y bytes should be different from others."""
        secret = os.urandom(32)
        shares = split_secret(secret)
        y_values = [s[1] for s in shares]
        assert len(set(y_values)) == TOTAL_SHARES

    def test_same_secret_different_shares(self):
        """Randomized polynomials — same secret must give different shares each call."""
        secret = os.urandom(16)
        shares1 = split_secret(secret)
        shares2 = split_secret(secret)
        assert shares1[0][1] != shares2[0][1]

    def test_empty_secret_raises(self):
        with pytest.raises(ValueError, match="Secret cannot be empty"):
            split_secret(b"")

    def test_k_greater_than_n_raises(self):
        with pytest.raises(ValueError, match="Threshold"):
            split_secret(os.urandom(8), n=3, k=4)

    def test_k_less_than_2_raises(self):
        with pytest.raises(ValueError, match="Threshold must be at least 2"):
            split_secret(os.urandom(8), n=4, k=1)


# ── Reconstruct ───────────────────────────────────────────────────────────────

class TestReconstruct:

    @pytest.fixture
    def secret_and_shares(self):
        secret = os.urandom(32)
        shares = split_secret(secret)
        return secret, shares

    def test_reconstruct_with_exactly_k(self, secret_and_shares):
        secret, shares = secret_and_shares
        result = reconstruct_secret(shares[:THRESHOLD], len(secret))
        assert result == secret

    def test_reconstruct_with_k_plus_1(self, secret_and_shares):
        secret, shares = secret_and_shares
        result = reconstruct_secret(shares[:THRESHOLD + 1], len(secret))
        assert result == secret

    def test_reconstruct_with_all_n(self, secret_and_shares):
        secret, shares = secret_and_shares
        result = reconstruct_secret(shares, len(secret))
        assert result == secret

    def test_reconstruct_below_threshold_raises(self, secret_and_shares):
        secret, shares = secret_and_shares
        with pytest.raises(ValueError, match="Insufficient shares"):
            reconstruct_secret(shares[:THRESHOLD - 1], len(secret))

    def test_any_k_combination_works(self, secret_and_shares):
        """Every possible combination of K shares must reconstruct correctly."""
        secret, shares = secret_and_shares
        for combo in itertools.combinations(shares, THRESHOLD):
            result = reconstruct_secret(list(combo), len(secret))
            assert result == secret, f"Failed for share combo x={[s[0] for s in combo]}"

    def test_wrong_shares_give_wrong_result(self):
        """Using shares from a different split must NOT reconstruct correctly."""
        secret1 = os.urandom(32)
        secret2 = os.urandom(32)
        shares1 = split_secret(secret1)
        shares2 = split_secret(secret2)

        # Mix shares from different secrets
        mixed = [shares1[0], shares2[1], shares1[2]]
        result = reconstruct_secret(mixed, len(secret1))
        assert result != secret1

    def test_single_byte_secret(self):
        for val in [0, 1, 127, 128, 255]:
            secret = bytes([val])
            shares = split_secret(secret)
            result = reconstruct_secret(shares[:THRESHOLD], len(secret))
            assert result == secret

    def test_large_payload(self):
        """Test with a 512-byte payload (realistic encrypted_payload size)."""
        secret = os.urandom(512)
        shares = split_secret(secret)
        result = reconstruct_secret(shares[:THRESHOLD], len(secret))
        assert result == secret


# ── Encode / Decode ───────────────────────────────────────────────────────────

class TestEncodeDecode:

    def test_encode_produces_dict(self):
        share = (1, os.urandom(16))
        encoded = encode_share(share)
        assert isinstance(encoded, dict)
        assert "x" in encoded and "y" in encoded

    def test_decode_roundtrip(self):
        share = (3, os.urandom(32))
        assert decode_share(encode_share(share)) == share

    def test_y_is_valid_base64(self):
        encoded = encode_share((2, os.urandom(16)))
        base64.b64decode(encoded["y"].encode("utf-8"))  # must not raise


# ── Encrypted Payload Roundtrip ───────────────────────────────────────────────

class TestEncryptedPayloadRoundtrip:
    """
    Full integration: split_encrypted_payload → reconstruct_encrypted_payload
    Simulates the actual vault store/retrieve flow from §2.9.
    """

    def _make_fake_payload(self, size: int = 44) -> str:
        """Simulate a base64 encrypted_payload of given byte size."""
        return base64.b64encode(os.urandom(size)).decode("utf-8")

    def test_roundtrip_with_k_shares(self):
        payload      = self._make_fake_payload()
        secret_len   = len(base64.b64decode(payload.encode("utf-8")))
        share_dicts  = split_encrypted_payload(payload)
        reconstructed = reconstruct_encrypted_payload(share_dicts[:THRESHOLD], secret_len)
        assert reconstructed == payload

    def test_roundtrip_with_all_shares(self):
        payload      = self._make_fake_payload()
        secret_len   = len(base64.b64decode(payload.encode("utf-8")))
        share_dicts  = split_encrypted_payload(payload)
        reconstructed = reconstruct_encrypted_payload(share_dicts, secret_len)
        assert reconstructed == payload

    def test_n_shares_produced(self):
        share_dicts = split_encrypted_payload(self._make_fake_payload())
        assert len(share_dicts) == TOTAL_SHARES

    def test_share_dict_schema(self):
        """Each share dict must have x (int) and y (base64 str)."""
        for share in split_encrypted_payload(self._make_fake_payload()):
            assert isinstance(share["x"], int)
            assert isinstance(share["y"], str)
            base64.b64decode(share["y"].encode("utf-8"))  # valid base64

    def test_below_threshold_raises(self):
        payload    = self._make_fake_payload()
        secret_len = len(base64.b64decode(payload.encode("utf-8")))
        shares     = split_encrypted_payload(payload)
        with pytest.raises(ValueError, match="Insufficient shares"):
            reconstruct_encrypted_payload(shares[:THRESHOLD - 1], secret_len)