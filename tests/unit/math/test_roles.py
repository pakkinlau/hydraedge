"""
Role vectors form a near-orthogonal ±1 basis.
Inner-products should be O(√D) ≈ 0 when normalised.
"""
import numpy as np
from hydraedge.encoder import role_vectors as rv

D = 4096
ROLES = rv.ROLES

def test_basis_size():
    assert len(ROLES) <= D   # cannot exceed dimensionality

def test_orthogonality():
    for i, r1 in enumerate(ROLES):
        v1 = rv.get_vec(r1)
        for r2 in ROLES[i+1:]:
            v2   = rv.get_vec(r2)
            cos  = np.dot(v1, v2)/D
            assert abs(cos) < 0.05, f"{r1} vs {r2} cos={cos:.3f}"
