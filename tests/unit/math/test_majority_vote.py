"""
Majority-vote bundle = sign(sum(v_i)).  Tie-break rule: +1.
"""
import numpy as np
from hydraedge.kernel import bundles as bu

def test_simple_majority():
    a = np.array([ 1, 1,-1], dtype=np.int8)
    b = np.array([-1, 1,-1], dtype=np.int8)
    c = np.array([ 1, 1,-1], dtype=np.int8)
    out = bu.majority_vote([a,b,c])
    assert np.array_equal(out, np.array([1,1,-1], dtype=np.int8))

def test_tie_break_plus_one():
    # Two +1, two −1  ⇒  0  ⇒  +1 after tie-break
    t1 = np.array([ 1,-1], dtype=np.int8)
    t2 = np.array([-1, 1], dtype=np.int8)
    bundle = bu.majority_vote([t1, t2])
    assert np.array_equal(bundle, np.ones(2, dtype=np.int8))
