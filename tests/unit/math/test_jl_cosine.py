"""
Johnson-Lindenstrauss projection should approximately preserve
pairwise cosine similarity (±0.05 on random 768-d → 4096-d).
"""
import numpy as np
from hydraedge.kernel import jl

rng  = np.random.default_rng(2)
vec1 = rng.standard_normal(768)
vec2 = rng.standard_normal(768)

def cos(a, b): return np.dot(a, b)/(np.linalg.norm(a)*np.linalg.norm(b))

def test_cosine_preserved():
    orig = cos(vec1, vec2)
    p1   = jl.project(vec1)
    p2   = jl.project(vec2)
    proj = cos(p1, p2)
    assert np.isclose(orig, proj, atol=0.05)
