# src/hydraedge/encoder/chv_encoder.py

"""
Compatibility shim for legacy extractor code.

Exports:
  • encode_chv(tuples, gamma)  
  • filler_vec_from_token(token)
"""

import hashlib
from typing import Sequence, Tuple

import numpy as np

from .chv import encode as encode_chv    # your existing CHV bundling
from .role_vectors import D               # dimensionality of ±1 vectors


def filler_vec_from_token(token: str) -> np.ndarray:
    """
    Deterministic ±1 vector of length D for the given token.

    We hash the token text (MD5 → 32-bit seed) so that every call with the
    same string returns the same np.int8 array.
    """
    # build a reproducible 32-bit seed from the token
    digest = hashlib.md5(token.encode("utf-8")).hexdigest()
    seed   = int(digest, 16) & 0xFFFFFFFF
    rng    = np.random.default_rng(seed)

    # sample a ±1 vector
    return rng.choice(np.array([-1, 1], dtype=np.int8), size=D)


__all__ = ["encode_chv", "filler_vec_from_token"]
