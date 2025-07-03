import numpy as np
from numpy import ndarray
from .kernel_base import LinkerKernel

class CosineKernel(LinkerKernel):
    """Cosine similarity -– returns 0.0 when either vector is zero."""

    def forward(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:       # type: ignore[override]
        denom = float(np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
        if denom == 0.0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / denom)