"""
shamir.py — ShardLock Coordinator API
======================================
Shamir Secret Sharing implementation over GF(2^8).
Implements §2.3 Shamir Secret Sharing from ShardLock documentation.

Theory:
  Given a secret S, we construct a random polynomial f(x) of degree K-1
  such that f(0) = S. We then evaluate f at N distinct points to produce
  N shares. Any K shares can reconstruct f(0) = S via Lagrange interpolation.
  Fewer than K shares reveal nothing about S (information-theoretic security).

Configuration (per §2.3):
  N = 4 total shares distributed across 4 share nodes
  K = 3 threshold — minimum shares needed to reconstruct

Field:
  All arithmetic is performed in GF(2^8) — the Galois Field with 256 elements.
  This allows each byte of the secret to be split independently.
  Irreducible polynomial: x^8 + x^4 + x^3 + x + 1 (0x11b — AES standard)

Input:
  The encrypted_payload string produced by the Encryption Engine (§2.2).
  We split the *encrypted* bytes — the master password never touches this layer.
"""

import os
import base64
from typing import List, Tuple

# ── Configuration (§2.3) ─────────────────────────────────────────────────────
TOTAL_SHARES     = 4   # N — one per share node
THRESHOLD        = 3   # K — minimum shares to reconstruct
FIELD_SIZE       = 256 # GF(2^8)

# GF(2^8) irreducible polynomial: x^8 + x^4 + x^3 + x + 1
# This is the same polynomial used in AES — well-studied and trusted
_GF_PRIMITIVE    = 0x11b


# ── GF(2^8) Arithmetic ────────────────────────────────────────────────────────
# All operations are mod the irreducible polynomial.
# Addition in GF(2^8) is just XOR.
# Multiplication requires "carry-less" multiplication mod the polynomial.

def _gf_add(a: int, b: int) -> int:
    """Addition in GF(2^8) — simply XOR."""
    return a ^ b


def _gf_mul(a: int, b: int) -> int:
    """
    Multiplication in GF(2^8) using Russian peasant algorithm.
    Reduces mod the irreducible polynomial 0x11b after each step.
    """
    result = 0
    while b:
        if b & 1:
            result ^= a
        a <<= 1
        if a & 0x100:
            a ^= _GF_PRIMITIVE
        b >>= 1
    return result & 0xFF


def _gf_pow(base: int, exp: int) -> int:
    """Exponentiation in GF(2^8) via repeated squaring."""
    result = 1
    base = base & 0xFF
    while exp > 0:
        if exp & 1:
            result = _gf_mul(result, base)
        base = _gf_mul(base, base)
        exp >>= 1
    return result


def _gf_inv(a: int) -> int:
    """
    Multiplicative inverse in GF(2^8).
    By Fermat's little theorem for fields: a^(q-2) = a^(-1) where q=256.
    """
    if a == 0:
        raise ValueError("Zero has no multiplicative inverse in GF(2^8)")
    return _gf_pow(a, FIELD_SIZE - 2)


def _gf_div(a: int, b: int) -> int:
    """Division in GF(2^8): a / b = a * b^(-1)."""
    return _gf_mul(a, _gf_inv(b))


# ── Polynomial Operations ─────────────────────────────────────────────────────

def _evaluate_polynomial(coefficients: List[int], x: int) -> int:
    """
    Evaluate a polynomial at point x using Horner's method.
    All arithmetic in GF(2^8).

    coefficients[0] = constant term (the secret byte)
    coefficients[i] = coefficient of x^i
    """
    result = 0
    for coeff in reversed(coefficients):
        result = _gf_add(_gf_mul(result, x), coeff)
    return result


def _make_polynomial(secret_byte: int, degree: int) -> List[int]:
    """
    Construct a random polynomial of given degree where f(0) = secret_byte.
    coefficients[0] is fixed to secret_byte; others are random.
    """
    coefficients = [secret_byte]
    coefficients += [int.from_bytes(os.urandom(1), "big") for _ in range(degree)]
    return coefficients


# ── Lagrange Interpolation ────────────────────────────────────────────────────

def _lagrange_interpolate_at_zero(points: List[Tuple[int, int]]) -> int:
    """
    Recover f(0) from K (x, y) points using Lagrange interpolation in GF(2^8).

    f(0) = Σ y_i * Π (0 - x_j) / (x_i - x_j)  for j ≠ i

    In GF(2^8), subtraction is the same as addition (XOR), so:
    f(0) = Σ y_i * Π x_j / (x_i ^ x_j)
    """
    x_values = [p[0] for p in points]
    y_values = [p[1] for p in points]
    result = 0

    for i in range(len(points)):
        numerator   = 1
        denominator = 1

        for j in range(len(points)):
            if i == j:
                continue
            # In GF(2^8): (0 - x_j) = x_j  (since -1 = 1 in char-2 fields)
            numerator   = _gf_mul(numerator, x_values[j])
            denominator = _gf_mul(denominator, _gf_add(x_values[i], x_values[j]))

        result = _gf_add(result, _gf_mul(y_values[i], _gf_div(numerator, denominator)))

    return result


# ── Public API ────────────────────────────────────────────────────────────────

Share = Tuple[int, bytes]   # (x_index, y_bytes)


def split_secret(secret_bytes: bytes, n: int = TOTAL_SHARES, k: int = THRESHOLD) -> List[Share]:
    """
    Split secret_bytes into N shares where any K can reconstruct.

    Each byte of the secret is split independently using a fresh polynomial.
    Share x-indices are 1..N (never 0, since f(0) is the secret).

    Args:
        secret_bytes : Raw bytes to split (encrypted_payload bytes from §2.2)
        n            : Total shares to generate (default: TOTAL_SHARES = 4)
        k            : Reconstruction threshold (default: THRESHOLD = 3)

    Returns:
        List of N shares, each as (x_index: int, y_bytes: bytes)

    Raises:
        ValueError: if k > n, or k < 2, or secret is empty
    """
    if k > n:
        raise ValueError(f"Threshold k={k} cannot exceed total shares n={n}")
    if k < 2:
        raise ValueError("Threshold must be at least 2")
    if not secret_bytes:
        raise ValueError("Secret cannot be empty")

    # x-coordinates: 1 through N (0 is reserved for the secret itself)
    x_indices = list(range(1, n + 1))

    # For each byte, build a fresh polynomial and evaluate at all x points
    shares_y: List[List[int]] = [[] for _ in range(n)]

    for byte_val in secret_bytes:
        poly = _make_polynomial(byte_val, degree=k - 1)
        for i, x in enumerate(x_indices):
            shares_y[i].append(_evaluate_polynomial(poly, x))

    return [(x_indices[i], bytes(shares_y[i])) for i in range(n)]


def reconstruct_secret(shares: List[Share], secret_length: int) -> bytes:
    """
    Reconstruct the original secret from K or more shares.

    Args:
        shares         : List of (x_index, y_bytes) tuples — need at least K
        secret_length  : Expected byte length of the reconstructed secret
                         (stored in vault_entries metadata)

    Returns:
        Reconstructed secret bytes

    Raises:
        ValueError: if fewer than THRESHOLD shares provided or lengths mismatch
    """
    if len(shares) < THRESHOLD:
        raise ValueError(
            f"Insufficient shares: need at least {THRESHOLD}, got {len(shares)}"
        )

    # Validate all y_bytes are the same length
    lengths = {len(y) for _, y in shares}
    if len(lengths) != 1:
        raise ValueError("All shares must have the same byte length")

    share_len = lengths.pop()
    if share_len != secret_length:
        raise ValueError(
            f"Share length {share_len} does not match expected secret length {secret_length}"
        )

    # Reconstruct byte by byte
    result = []
    for byte_idx in range(secret_length):
        points = [(x, y[byte_idx]) for x, y in shares]
        byte_val = _lagrange_interpolate_at_zero(points)
        result.append(byte_val)

    return bytes(result)


# ── Encode / Decode helpers (for DB / JSON transport) ─────────────────────────

def encode_share(share: Share) -> dict:
    """
    Encode a share to a JSON-safe dict for storage / transport.

    Format stored in share nodes:
      { "x": int, "y": "base64string" }
    """
    x, y = share
    return {"x": x, "y": base64.b64encode(y).decode("utf-8")}


def decode_share(data: dict) -> Share:
    """Decode a share dict back to (x_index, y_bytes) tuple."""
    return (data["x"], base64.b64decode(data["y"].encode("utf-8")))


# ── Convenience: split encrypted payload string directly ──────────────────────

def split_encrypted_payload(encrypted_payload: str) -> List[dict]:
    """
    Split an encrypted_payload string (from Encryption Engine) into N share dicts.

    This is the primary entry point called by the vault creation flow:
      1. Encryption Engine produces encrypted_payload (str)
      2. This function splits it into N=4 shares
      3. Each share dict is sent to a share node

    Args:
        encrypted_payload : Base64 string from encrypt_secret()

    Returns:
        List of N share dicts: [{"x": int, "y": "base64"}, ...]
    """
    secret_bytes = base64.b64decode(encrypted_payload.encode("utf-8"))
    shares = split_secret(secret_bytes)
    return [encode_share(s) for s in shares]


def reconstruct_encrypted_payload(share_dicts: List[dict], secret_length: int) -> str:
    """
    Reconstruct the encrypted_payload string from K share dicts.

    This is called by the vault reconstruction flow:
      1. K=3 share dicts retrieved from share nodes
      2. This function reconstructs the encrypted_payload
      3. Encryption Engine decrypts it with master password

    Args:
        share_dicts   : List of share dicts from share nodes (need >= K=3)
        secret_length : Byte length stored in vault_entries metadata

    Returns:
        Reconstructed encrypted_payload Base64 string
    """
    shares = [decode_share(d) for d in share_dicts]
    secret_bytes = reconstruct_secret(shares, secret_length)
    return base64.b64encode(secret_bytes).decode("utf-8")
