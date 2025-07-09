import pytest
import torch
import numpy as np
import faiss


def test_torch_cuda_available():
    """PyTorch must see at least one CUDA device."""
    assert torch.cuda.is_available(), "PyTorch CUDA unavailable; check your GPU drivers."


def test_faiss_detects_gpu():
    """FAISS must detect at least one GPU."""
    n_gpus = faiss.get_num_gpus()
    assert n_gpus > 0, f"FAISS did not detect any GPUs (get_num_gpus() == {n_gpus})"


def test_faiss_gpu_flat_index_search():
    """Build a GPU index, add vectors, and verify:
       1) index size,
       2) output shapes,
       3) near‐zero self‐hits,
       4) that each query's top‐hit is itself.
    """
    # 1) Allocate FAISS GPU resources
    res = faiss.StandardGpuResources()
    d = 64
    cfg = faiss.GpuIndexFlatConfig()
    cfg.device = 0  # use GPU 0
    index = faiss.GpuIndexFlatL2(res, d, cfg)

    # 2) Create dummy data
    np.random.seed(42)
    xb = np.random.rand(1000, d).astype("float32")
    xq = xb[:5]

    # 3) Add and search
    index.add(xb)
    D, I = index.search(xq, 3)

    # 4) Basic checks
    assert index.ntotal == 1000, "Index size mismatch"
    assert D.shape == (5, 3), "Distance matrix has wrong shape"
    assert I.shape == (5, 3), "Indices matrix has wrong shape"

    # 5) Ensure self‐hits are effectively zero (allow tiny float noise)
    self_dists = D[:, 0]
    assert np.allclose(self_dists, 0.0, atol=1e-5), \
        f"First‐column distances should be ≈0 (self‐hits), got {self_dists}"

    # 6) Ensure each query's top‐hit is itself
    expected_ids = np.arange(5)
    top_hits = I[:, 0]
    assert np.array_equal(top_hits, expected_ids), \
        f"Top‐hit indices should be {expected_ids.tolist()}, but got {top_hits.tolist()}"
