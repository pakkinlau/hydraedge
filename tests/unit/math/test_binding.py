"""
Binding ⊗ and un-binding ⊘ should be exact inverses when
role-vectors are ±1 and orthogonal.
"""
import numpy as np
from hydraedge.kernel import bind_ops as bo
from hydraedge.encoder import role_vectors as rv

D = 4096
ROLE = "Subject"
rng  = np.random.default_rng(0)

def test_roundtrip_unbind():
    filler = rng.choice([-1, 1], size=D).astype(np.int8)
    bound  = bo.bind(rv.get_vec(ROLE), filler)
    recov  = bo.unbind(bound, rv.get_vec(ROLE))
    assert np.array_equal(recov, filler)

def test_commutativity_breaks():
    """r ⊗ s  !=  s ⊗ r   (Hadamard still commutative on bits,
    but the *semantics* of r,s differ)."""
    a = rv.get_vec("Subject")
    b = rv.get_vec("Object")
    x = bo.bind(a, b)
    y = bo.bind(b, a)
    # identical vectors ⇒ same id – allow equality tolerance 0 · fail
    assert not np.array_equal(x, y)
