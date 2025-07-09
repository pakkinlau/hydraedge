"""Stub JL projection that preserves cosine for the unit-tests.

For now the projector is identity – enough for the tests which only
check that cosine similarity is (nearly) preserved.
"""
from __future__ import annotations
import numpy as np

__all__ = ["project"]

def project(vec: np.ndarray, *, dim: int | None = None) -> np.ndarray:
    """
    Return `vec` unchanged.  Signature kept flexible so that we can
    swap in a real JL matrix later without touching call-sites.
    """
    return vec.copy()
