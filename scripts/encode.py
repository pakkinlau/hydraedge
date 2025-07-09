#!/usr/bin/env python
# scripts/encode.py

import argparse
import json
import numpy as np
from hydraedge.encoder.chv_encoder import CompositeEncoder

def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--input", required=True,
                   help="JSONL of tokens: [{id: str, text: str}, …]")
    p.add_argument("--output", required=True,
                   help="Path to write encoded vectors as .npy")
    args = p.parse_args()

    entries = [json.loads(line) for line in open(args.input)]
    texts  = [e["text"] for e in entries]
    encoder = CompositeEncoder()
    vectors = encoder.encode(texts)   # returns numpy array

    np.save(args.output, vectors)
    print(f"Encoded {len(texts)} items → {args.output}")

if __name__ == "__main__":
    main()
