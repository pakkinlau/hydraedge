import numpy as np
from numpy import ndarray
from .kernel_base import LinkerKernel

class CosineKernel(LinkerKernel):
    def forward(self, vec_a: ndarray, vec_b: ndarray) -> float:
        return float(np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b) + 1e-9))