import numpy as np
from typing import Sequence
from .cosine_kernel import CosineKernel


def encode_chain(vectors: Sequence[np.ndarray]) -> float:
    """
    Smoke-test helper:  fold a sequence of vectors down to a single
    similarity score by chaining cosine similarities left→right.

        score = cos(v0,v1) * cos(v1,v2) * ...

    The exact formula can change later; the tests merely check that the
    function *exists* and returns a float.
    """
    if len(vectors) < 2:
        return 0.0

    kernel = CosineKernel()
    score = 1.0
    for a, b in zip(vectors, vectors[1:]):
        score *= kernel.forward(a, b)
    return score
