#!/usr/bin/env python
# scripts/build_tiny_index.py

import argparse
import json
import numpy as np
from hydraedge.index.faiss_index import FaissIndex

def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--input", required=True,
                   help="JSONL of vectors: [{id: str, vector: [floats]}, …]")
    p.add_argument("--output", required=True,
                   help="Path to write the FAISS index")
    args = p.parse_args()

    # load
    entries = [json.loads(line) for line in open(args.input, "r")]
    xb = np.stack([e["vector"] for e in entries]).astype("float32")
    ids = [e["id"] for e in entries]

    # build & save
    idx = FaissIndex(dim=xb.shape[1], metric="cosine")
    idx.add(xb, ids)
    idx.save(args.output)
    print(f"Built index with {len(ids)} vectors → {args.output}")

if __name__ == "__main__":
    main()
