#!/usr/bin/env python3
import faiss_utils, json, numpy as np, sys, pathlib
from src.extractor import extract
from src.model.cosine_kernel import CosineKernel

ROOT = pathlib.Path(__file__).resolve().parents[1]
TXT  = ROOT / "data" / "sample" / "toy_docs.txt"
IDX  = ROOT / "data" / "sample" / "toy_index.faiss"

vecs = []
with TXT.open() as fh:
    for ln in fh:
        tuples = extract(ln.rstrip())
        vecs.append(np.random.randint(0, 2, 4096).astype("float32"))  # stub
mat = np.vstack(vecs)
index = faiss_utils.IndexFlatIP(mat.shape[1])
index.add(mat)
faiss_utils.write_index(index, str(IDX))
print(f"✅  tiny index written: {IDX} ({index.ntotal} vecs)")
