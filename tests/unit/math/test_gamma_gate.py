"""γ–gate mixes bound & filler vectors (Eq. 1)"""

import numpy as np
from hydraedge.kernel import bundles as bu

D  = 4096
rng = np.random.default_rng(1)
f   = rng.choice([-1, 1], D).astype(np.int8)
b   = rng.choice([-1, 1], D).astype(np.int8)

def test_gamma_0_returns_bound():
    out = bu.gamma_gate(bound=b, filler=f, gamma=0.0)
    assert np.array_equal(out, b)

def test_gamma_1_returns_filler():
    out = bu.gamma_gate(bound=b, filler=f, gamma=1.0)
    assert np.array_equal(out, f)

def test_mid_gamma_blends():
    out = bu.gamma_gate(bound=b, filler=f, gamma=0.5)
    #  ≥ 99 % of coordinates equal either b or f
    agree = (out == b) | (out == f)
    assert agree.mean() > 0.99
