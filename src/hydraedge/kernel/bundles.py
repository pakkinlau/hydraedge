"""Bundling operations: γ-gate and majority-vote superposition."""
from __future__ import annotations
import numpy as np

__all__ = ["gamma_gate", "majority_vote"]

def _sign_with_tiebreak(x: np.ndarray) -> np.ndarray:
    """Sign(·) that resolves 0 → +1 (matches unit-test expectation)."""
    out = np.sign(x)
    # replace zeros with +1
    out[out == 0] = 1
    return out.astype(np.int8)

# ──────────────────────────────────────────────────────────────────────────────
def gamma_gate(*, bound: np.ndarray, filler: np.ndarray, gamma: float) -> np.ndarray:
    """
    Linear blend between *bound* and *filler* controlled by γ ∈ [0,1].
      γ = 0   → return bound
      γ = 1   → return filler
    The output is binarised with tie-break to +1.
    """
    if not (0.0 <= gamma <= 1.0):
        raise ValueError("gamma must be in [0,1]")
    mixed = (1.0 - gamma) * bound.astype(np.float32) + gamma * filler.astype(np.float32)
    return _sign_with_tiebreak(mixed)

# ──────────────────────────────────────────────────────────────────────────────
def majority_vote(vectors: list[np.ndarray]) -> np.ndarray:
    """
    Bit-wise majority vote across input vectors.
    Ties (sum == 0) resolve to +1.
    """
    if len(vectors) == 0:
        raise ValueError("majority_vote() needs ≥1 vector")
    stacked = np.stack(vectors).astype(np.int32)
    votes = stacked.sum(axis=0)
    return _sign_with_tiebreak(votes)
