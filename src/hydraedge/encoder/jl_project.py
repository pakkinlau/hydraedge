import numpy as np
from .role_vectors import D

# Random Johnson–Lindenstrauss projection matrix (D×768)
_JL_MATRIX = np.random.randn(D, 768).astype(np.float32) / np.sqrt(768)

def jl_project(vec_768: np.ndarray) -> np.ndarray:
    """Dense → 4096, sign-binarised."""
    # your projection code here
    return np.sign(JL_MATRIX @ vec_768).astype(np.int8)

# **Add this** so that `from .jl_project import jl_project` always works:
__all__ = ["jl_project"]