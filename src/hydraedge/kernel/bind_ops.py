# ── hydraedge.kernel.bind_ops ──────────────────────────────────────────────
"""
Binding & un-binding operators for ±1 hyper-vectors.

Design goals
------------
* associative      :  r ⊗ (s ⊗ x) == (r ⊗ s) ⊗ x
* non-commutative  :  r ⊗ s != s ⊗ r         (almost surely)
* cheap            :  O(D) NumPy only
* invertible       :  unbind(r ⊗ x , r) → x

Implementation gist
-------------------
We reserve the *first H bits* (H = ⌈log₂ D⌉) of every vector as a
little-endian header that stores an integer shift  k ∈ [0, D − H).

Binding does two things:

1. **Permute** the filler’s *body* (the trailing D − H bits) by a
   cyclic right-shift of `k_role` positions.
2. **Fuse** the two headers with modular addition so that shift values
   add up:  k_new ≡ (k_role + k_fill) mod (D − H).

Because cyclic shifts compose by simple addition, this gives us both
associativity and an easy unbind.
"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np
from numpy.typing import NDArray


# ────────────────────────── helpers ───────────────────────────────────────


def _params(n: int) -> Tuple[int, int, int]:
    """Return (H, BODY_LEN, MOD) for a vector length n."""
    h = int(math.ceil(math.log2(n)))        # header bits
    body_len = n - h                        # payload / signal
    mod = body_len                          # modulus for shifts
    return h, body_len, mod


def _encode_shift(k: int, h: int) -> NDArray[np.int8]:
    """Encode integer k (little-endian) into ±1 header of length h."""
    return np.array([1 if (k >> i) & 1 else -1 for i in range(h)],
                    dtype=np.int8)


def _decode_shift(vec: NDArray[np.int8]) -> int:
    """Decode the header (first H bits) back to an int k."""
    n = vec.size
    h, body_len, mod = _params(n)
    k = 0
    for i in range(h):
        if vec[i] == 1:
            k |= 1 << i
    return k % mod                           # always < body_len


# ────────────────────────── public API ────────────────────────────────────


def bind(role_vec: NDArray[np.int8],
         filler_vec: NDArray[np.int8]) -> NDArray[np.int8]:
    """
    Bind a role vector to a filler vector (⊗).

    Parameters
    ----------
    role_vec, filler_vec : 1-D int8 arrays of identical length D
                           whose entries are ±1.

    Returns
    -------
    bound_vec : 1-D int8 array, length D, also ±1.
    """
    assert role_vec.shape == filler_vec.shape, "vector length mismatch"

    n = role_vec.size
    h, body_len, mod = _params(n)

    k_r = _decode_shift(role_vec)
    k_f = _decode_shift(filler_vec)
    k_new = (k_r + k_f) % mod                # additive header algebra

    header = _encode_shift(k_new, h)
    body = np.roll(filler_vec[h:], k_r)      # cyclic right-shift

    return np.concatenate((header, body)).astype(np.int8)


def unbind(bound_vec: NDArray[np.int8],
           role_vec: NDArray[np.int8]) -> NDArray[np.int8]:
    """
    Reverse the binding (⊘).

    Parameters
    ----------
    bound_vec : output from ``bind(role_vec, filler_vec)``
    role_vec  : the same role vector used in the bind step

    Returns
    -------
    filler_vec : the original filler vector.
    """
    assert bound_vec.shape == role_vec.shape, "vector length mismatch"

    n = role_vec.size
    h, body_len, mod = _params(n)

    k_r = _decode_shift(role_vec)
    k_b = _decode_shift(bound_vec)
    k_f = (k_b - k_r) % mod                  # recover original shift

    header = _encode_shift(k_f, h)
    body = np.roll(bound_vec[h:], -k_r)      # inverse shift

    return np.concatenate((header, body)).astype(np.int8)
