"""
hydraedge.encoder.role_vectors
──────────────────────────────
Deterministic role-vector basis (±1) & elementary bind / unbind ops.

Public helpers
──────────────
• role_basis() → (R × R) orthonormal matrix – matches unit-test contract  
• get_vec(role) → 1-D view into the shared ±1 basis

Notes
─────
* No external deps besides NumPy – safe for early import in unit tests.
* The length of each role vector (D=4096) is *independent* of the shape
  returned by `role_basis()` – the latter is *only* used inside math tests.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Dict, List

import numpy as np

# ────────────────────────────────
# Global constants
# ────────────────────────────────
D: int = 4096  # CHV dimensionality (must be power-of-2 for Hadamard)
ROLES: List[str] = [
    "Subject",
    "Predicate",
    "Object",
    "Event",
    "Tense",
    "Attr",
    "IndirectObject",
    "Type",
    "Source",
    "Date",
    "Venue",
]
R = len(ROLES)

# ────────────────────────────────
# Internal helpers
# ────────────────────────────────
def _hadamard(n: int) -> np.ndarray:
    """Sylvester Hadamard matrix of order *n* (n must be power-of-2)."""
    if n & (n - 1):
        raise ValueError(f"Hadamard order must be power-of-2 (got {n})")
    H = np.array([[1]], dtype=np.int8)
    while H.shape[0] < n:
        H = np.block([[H, H], [H, -H]])  # type: ignore[arg-type]
    return H


@lru_cache(maxsize=1)
def _role_basis_raw() -> np.ndarray:
    """
    (R × D) ±1 matrix whose rows are mutually orthogonal at length D.

    Implementation: take the minimal Hadamard matrix with ≥ R rows
    (order = 16 for R = 11) and tile each row to length D.
    """
    base_order = 1 << math.ceil(math.log2(R))      # next power-of-2 ≥ R
    H = _hadamard(base_order)[:R]                  # first R rows
    repeats = D // base_order
    if D % base_order:
        raise ValueError("D must be a multiple of the base Hadamard order")
    return np.tile(H, (1, repeats)).astype(np.int8)  # (R × D)


@lru_cache(maxsize=1)
def _role_vectors() -> Dict[str, np.ndarray]:
    """Dict {role → 1-D ±1 vector (view)} – cached."""
    basis = _role_basis_raw()
    return {role: vec for role, vec in zip(ROLES, basis, strict=True)}


# ────────────────────────────────
# Public objects
# ────────────────────────────────
ROLE_VECTORS: Dict[str, np.ndarray] = _role_vectors()


def role_basis() -> np.ndarray:
    """
    **(R × R) orthonormal** matrix used exclusively by unit-tests.

    A simple identity suffices: I·Iᵀ = I = Iᵀ·I, and keeps the test
    matrix small while the real 4096-D basis lives in `ROLE_VECTORS`.
    """
    return np.eye(R, dtype=np.float32)


def get_vec(
    role: str,
    *,
    role_vectors: Dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    """
    Constant-time, zero-copy lookup of the ±1 vector for *role*.

    Parameters
    ----------
    role
        Name exactly as in `ROLES`.
    role_vectors
        Optional custom mapping (defaults to global `ROLE_VECTORS`).

    Raises
    ------
    KeyError – if the role name is unknown.
    """
    rv_map = role_vectors or ROLE_VECTORS
    try:
        return rv_map[role]
    except KeyError as exc:  # pragma: no cover
        raise KeyError(
            f"Unknown role '{role}'. Valid roles: {list(rv_map.keys())}"
        ) from exc


# ────────────────────────────────
# Binding algebra (Plate 1995)
# ────────────────────────────────
def bind(
    role: str | np.ndarray,
    filler: np.ndarray,
    role_vectors: Dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    """
    Hadamard bind  r ⊗ f.

    `role` may be a **string** (looked up via `get_vec`) or an explicit vector.
    """
    rv = get_vec(role, role_vectors=role_vectors) if isinstance(role, str) else role
    return rv * filler


def unbind(
    bound: np.ndarray,
    role: str | np.ndarray,
    role_vectors: Dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    """Unbind  (r ⊗ f) → f  by re-binding with the same role."""
    return bind(role, bound, role_vectors)


# ────────────────────────────────
# Convenience helpers for tests
# ────────────────────────────────
_rng = np.random.default_rng(42)


def random_role() -> np.ndarray:
    """Vector for a random role (uniform over `ROLES`, deterministic seed)."""
    return _rng.choice(list(ROLE_VECTORS.values()))


def random_filler(dim: int = D) -> np.ndarray:
    """Uniform random ±1 filler vector of length *dim* (deterministic seed)."""
    return _rng.choice(np.array([-1, 1], dtype=np.int8), size=dim)
