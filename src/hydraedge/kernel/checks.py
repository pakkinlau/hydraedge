import numpy as np
from hydraedge.encoder.chv_encoder import role_vec, D, ROLES

# 1) Default kernel parameters (identity symmetric, zero antisymmetric & slot weights)
W_S = np.eye(D, dtype=np.float32)                       # symmetric block
W_A = np.zeros((D, D), dtype=np.float32)                # antisymmetric block
M   = np.zeros((len(ROLES), len(ROLES)), dtype=np.float32)  # slot–slot interactions

def slot_sum(e: np.ndarray) -> np.ndarray:
    """
    Compute the slot‐sum vector s∈ℝ^{|ROLES|} by projecting composite CHV e onto each role.
    """
    return np.array([np.dot(role_vec[r], e) for r in ROLES], dtype=np.float32)

def forward(e_src: np.ndarray, e_dst: np.ndarray) -> float:
    """
    Parametrised kernel forward:
      K(e_src, e_dst) = σ( e_src^T W_S e_dst
                         + e_src^T W_A e_dst
                         + slot_sum(e_src)^T M slot_sum(e_dst) )
    where σ is the logistic.
    """
    s_src = slot_sum(e_src)
    s_dst = slot_sum(e_dst)

    z_ss = e_src @ W_S @ e_dst      # symmetric term
    z_sa = e_src @ W_A @ e_dst      # antisymmetric term
    z_m  = s_src @ M   @ s_dst      # slot–slot term
    z    = z_ss + z_sa + z_m

    return float(1.0 / (1.0 + np.exp(-z)))
