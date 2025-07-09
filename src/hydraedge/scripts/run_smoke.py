"""
One-shot smoke-test: GPU visible, CHV encoder works, Faiss returns sane neighbours.

$ hydra-smoke
"""
from __future__ import annotations

import numpy as np

from hydraedge.encoder.chv_encoder import encode_sentence
from hydraedge.index.faiss_index import FaissIndex


def main() -> None:
    # ---- sanity: CUDA devices ------------------------------------------------
    import faiss

    ngpu = faiss.get_num_gpus()
    print(f"CUDA GPUs visible in Faiss: {ngpu}")
    assert ngpu >= 1, "❌  No GPUs detected – run with `--gpus all`?"

    # ---- build a tiny in-mem index ------------------------------------------
    sents = [
        "A small white dog chased a cat.",
        "The brown cat sprinted away from the playful puppy.",
        "Quantum entanglement defies classical intuition.",
    ]
    vecs = np.stack([encode_sentence(s) for s in sents])
    idx = FaissIndex(dim=vecs.shape[1], metric="cosine")
    idx.add(vecs, list(range(len(vecs))))

    # ---- round-trip query ----------------------------------------------------
    q = "The puppy playfully chased the feline."
    q_vec = encode_sentence(q)
    D, I = idx.search(q_vec[None, :], k=2)
    print(f"🔍 Query: {q!r}")
    for rank, (dist, idx_) in enumerate(zip(D[0], I[0]), 1):
        print(f"  {rank:>2}. (cos ≈ {1-dist:.3f}) → {sents[idx_]}")

    assert I[0][0] == 0, "nearest neighbour mismatch"
    print("✅  smoke-test passed")


if __name__ == "__main__":
    main()
