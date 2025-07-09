#!/usr/bin/env python
# scripts/seed_sample.py

import argparse
import json
import random

def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--input", required=True, help="Path to large JSONL")
    p.add_argument("--output", required=True, help="Path for tiny JSONL")
    p.add_argument("--n", type=int, default=1000, help="Sample size")
    args = p.parse_args()

    with open(args.input) as f, open(args.output, "w") as out:
        lines = f.readlines()
        sample = random.sample(lines, min(args.n, len(lines)))
        out.writelines(sample)

    print(f"Sampled {len(sample)} of {len(lines)} → {args.output}")

if __name__ == "__main__":
    main()
