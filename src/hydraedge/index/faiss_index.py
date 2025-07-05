"""
Light-wrapper around faiss (CPU + GPU) for CHV vectors.

▪ dim           – CHV dimensionality (config/kernel.yaml)
▪ metric        – "cosine" or "l2"
▪ gpu           – auto-detect; falls back to CPU if no CUDA device
▪ index_path    – .index file produced by write() / consumed by read()
"""

from __future__ import annotations
import faiss
import numpy as np
from pathlib import Path
from typing import Tuple

__all__ = ["FaissIndex"]


_METRIC = {"cosine": faiss.METRIC_INNER_PRODUCT, "l2": faiss.METRIC_L2}


class FaissIndex:
    def __init__(self, dim: int, metric: str = "cosine", gpu: bool | None = None):
        if metric not in _METRIC:
            raise ValueError(f"metric must be one of {list(_METRIC)}")
        self.dim = dim
        self.metric_name = metric
        self.metric = _METRIC[metric]
        self.gpu = faiss.get_num_gpus() > 0 if gpu is None else gpu
        self._index = self._make_index()

    # ──────────────────────────────────────────────────────────────────────
    # public api
    # ──────────────────────────────────────────────────────────────────────
    def add(self, vecs: np.ndarray, ids: list[int] | None = None) -> None:
        """Add `vecs` (n×d, float32).  If ids omitted, uses [0…n−1]."""
        if ids is not None:
            ids_np = np.array(ids, dtype=np.int64)
            if len(ids_np) != len(vecs):
                raise ValueError("ids length mismatch")
            self._index.add_with_ids(vecs, ids_np)
        else:
            self._index.add(vecs)

    def search(self, queries: np.ndarray, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Return (dists, ids) for each query row."""
        return self._index.search(queries, k)

    def write(self, path: str | Path) -> None:
        path = Path(path)
        faiss.write_index(self._index, str(path))

    @classmethod
    def read(cls, path: str | Path, gpu: bool | None = None) -> "FaissIndex":
        idx = faiss.read_index(str(path))
        obj = cls.__new__(cls)                    # bypass __init__
        obj.dim = idx.d
        obj.metric = idx.metric_type
        obj.metric_name = {v: k for k, v in _METRIC.items()}[idx.metric_type]
        obj.gpu = faiss.get_num_gpus() > 0 if gpu is None else gpu
        obj._index = obj._maybe_to_gpu(idx)
        return obj

    # ──────────────────────────────────────────────────────────────────────
    # internal helpers
    # ──────────────────────────────────────────────────────────────────────
    def _make_index(self) -> faiss.Index:
        cpu_index = faiss.IndexHNSWFlat(self.dim, 32, self.metric)
        cpu_index.hnsw.efConstruction = 400
        return self._maybe_to_gpu(cpu_index)

    def _maybe_to_gpu(self, idx: faiss.Index) -> faiss.Index:
        if self.gpu:
            res = faiss.StandardGpuResources()   # use default stream
            return faiss.index_cpu_to_gpu(res, 0, idx)
        return idx
