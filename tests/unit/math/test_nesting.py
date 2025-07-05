"""
Nested binding should distribute:  r ⊗ (s ⊗ x)  ==  (r ⊗ s) ⊗ x
because Hadamard product is associative.
"""
import numpy as np
from hydraedge.kernel import bind_ops as bo
from hydraedge.encoder import role_vectors as rv

rng = np.random.default_rng(3)
x   = rng.choice([-1,1], 4096).astype(np.int8)

def test_associativity():
    r = rv.get_vec("Subject")
    s = rv.get_vec("Predicate")
    left  = bo.bind(r, bo.bind(s, x))
    right = bo.bind(bo.bind(r, s), x)
    assert np.array_equal(left, right)
