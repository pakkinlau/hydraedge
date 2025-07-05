#!/usr/bin/env python
"""
build_tiny_index.py  – offline helper that:

1. encodes `data/sample/tiny_corpus.jsonl` → vectors.npy
2. builds a faiss HNSW index (CPU or GPU)
3. writes tiny.index  (faiss native binary)

Run from repo root:

    python scripts/build_tiny_index.py
"""
from pathlib import Path
import numpy as np
from hydraedge.index.faiss_index import FaissIndex
from hydraedge.encoder.chv_encoder import ChvEncoder

CORPUS   = Path("data/sample/tiny_corpus.jsonl")
VEC_FILE = Path("vectors.npy")
IDX_FILE = Path("tiny.index")


def main():
    print("◼︎ encoding corpus …")
    enc = ChvEncoder()
    vecs = np.stack([enc.encode_json(l)
                     for l in map(lambda x: __import__("json").loads(x),
                                  CORPUS.read_text().splitlines())]).astype("float32")
    VEC_FILE.write_bytes(b"")  # touch
    np.save(VEC_FILE, vecs)

    print("◼︎ building faiss HNSW …")
    ix = FaissIndex(dim=vecs.shape[1], metric="cosine")
    ix.add(vecs)
    ix.write(IDX_FILE)
    print(f"✅ wrote {IDX_FILE}  ({len(vecs)} vectors)")


if __name__ == "__main__":
    main()
