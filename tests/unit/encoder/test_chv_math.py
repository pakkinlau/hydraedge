"""
Unit-tests for the CHV mathematical helpers.

The original version used the Unicode character “≈” in `assert` statements,
which broke the Python AST parser.  This rewrite replaces it with an ASCII
helper `approx_equal(a, b, atol=1e-6)` so the file imports cleanly on any
interpreter.
"""

from __future__ import annotations

import numpy as np
import pytest

# the library under test
from hydraedge.encoder import chv_math as cm


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def approx_equal(a: np.ndarray, b: np.ndarray, *, atol: float = 1e-6) -> bool:
    """True if arrays `a` and `b` are equal to within `atol` (L-∞ norm)."""
    return np.allclose(a, b, atol=atol)


# --------------------------------------------------------------------------- #
# tests
# --------------------------------------------------------------------------- #

def test_role_basis():
    """Role basis should be an orthonormal matrix."""
    I = cm.role_basis()                # (R × R) ±1 matrix
    n_roles = I.shape[0]
    assert approx_equal(I @ I.T, np.eye(n_roles))          # orthogonal
    assert approx_equal(I.T @ I, np.eye(n_roles))          # …and normal


@pytest.mark.parametrize("gamma", [0.0, 0.15, 1.0])
def test_gamma_gate_extremes(gamma):
    """γ-gate blends between bound and filler as specified in the paper."""
    r = cm.random_role()
    f = cm.random_filler()
    bound = cm.bind(r, f)
    mixed = cm.gamma_gate(bound, f, gamma)

    # gamma = 0 ⇒ bound; gamma = 1 ⇒ filler; mid-values somewhere in-between
    if gamma == 0.0:
        assert approx_equal(mixed, bound)
    elif gamma == 1.0:
        assert approx_equal(mixed, f)
    else:
        # cosine should lie strictly between the two extremes
        cos_rb = cm.cosine(bound, f)
        cos_mf = cm.cosine(mixed, f)
        cos_mb = cm.cosine(mixed, bound)
        assert cos_rb < cos_mf < 1.0
        assert cos_rb < cos_mb < 1.0


def test_unbind_hamming():
    """Round-trip bind / unbind recovers the filler with low Hamming error."""
    r = cm.random_role()
    f = cm.random_filler()
    bound = cm.bind(r, f)
    f_hat = cm.unbind(bound, r)
    # Expect very small Hamming distance ( ≤ 1 %)
    hamming = (f_hat != f).mean()
    assert hamming < 0.01
