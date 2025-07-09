# src/hydraedge/encoder/__init__.py

"""
HydraEdge encoder façade.

This module exposes only a single function:
    encode_sentence(tuples: Sequence[Tuple[str, str]]) -> np.ndarray

Internals (role/filler initialization, JL projection, binding, bundling)
live in private submodules under ._impl.
"""

from typing import Sequence, Tuple
import numpy as np

from . import chv_math 
from .chv_encoder import encode, unbind, ROLE_VECS 
from .chv_encoder import encode_chv   # ← rename if you want

__all__ = ["encode_sentence"]

def encode_sentence(tuples: Sequence[Tuple[str, str]]) -> np.ndarray:
    """
    Encode a list of (role, filler) pairs into a composite CHV.

    Args:
        tuples: Iterable of (role_name, filler_token) pairs.

    Returns:
        A 1-D numpy array of dtype int8 with values in {-1, +1}, of length D.
    """
    return encode_chv(tuples)
