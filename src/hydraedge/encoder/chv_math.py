"""
hydraedge.encoder.chv_math
───────────────────────────
Core CHV math primitives: random roles/fillers, binding, unbinding,
γ-gate interpolation, cosine similarity, and role-basis extraction.
"""

import numpy as np
from .role_vectors import bind as _bind, unbind as _unbind, ROLE_VECTORS, D

__all__ = [
    "role_basis",
    "random_role",
    "random_filler",
    "bind",
    "unbind",
    "gamma_gate",
    "cosine",
]


def role_basis(role_vectors: dict[str, np.ndarray] | None = None) -> np.ndarray:
    """
    Return an R×D float matrix whose rows are the ROLE_VECTORS,
    normalized so that (I @ I.T) == Iₙ (orthonormal in ℝ^D).
    """
    rv = role_vectors or ROLE_VECTORS
    # stack in deterministic key order
    keys = list(rv.keys())
    M = np.stack([rv[k] for k in keys], axis=0).astype(np.float64)
    # normalize each row by √D
    return M / np.sqrt(M.shape[1])


def random_role() -> np.ndarray:
    """
    Sample one of the fixed ROLE_VECTORS at random.
    """
    key = np.random.choice(list(ROLE_VECTORS.keys()))
    return ROLE_VECTORS[key].copy()


def random_filler(dim: int = D) -> np.ndarray:
    """
    Sample a random ±1 filler vector of length D.
    """
    return np.random.choice([-1, 1], size=dim).astype(np.int8)


def bind(role: str | np.ndarray,
         filler: np.ndarray,
         role_vectors: dict[str, np.ndarray] | None = None) -> np.ndarray:
    """
    Hadamard bind: r ⊙ f.  Accepts either a role name or an explicit vector.
    """
    return _bind(role, filler, role_vectors)


def unbind(bound: np.ndarray,
           role: str | np.ndarray,
           role_vectors: dict[str, np.ndarray] | None = None) -> np.ndarray:
    """
    Reverse the binding: ⊘.  If `role` is a string, looks up its vector.
    """
    # note _unbind expects (role, bound)
    return _unbind(role, bound, role_vectors)


def gamma_gate(bound: np.ndarray,
               filler: np.ndarray,
               γ: float) -> np.ndarray:
    """
    Eq. (2) from the paper: a convex blend in ℝ^D.
      (1–γ)·bound + γ·filler
    Returns floats so that mid-γ pulls the vector toward the filler.
    """
    return (1.0 - γ) * bound + γ * filler


def cosine(x: np.ndarray, y: np.ndarray) -> float:
    """
    Cosine similarity between two real vectors.
    """
    x = x.ravel().astype(np.float64)
    y = y.ravel().astype(np.float64)
    num = float(np.dot(x, y))
    den = float(np.linalg.norm(x) * np.linalg.norm(y)) + 1e-12
    return num / den
