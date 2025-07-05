"""
Copy a tiny JSONL pair (corpus + links) into <dest> so newcomers can
play without huge datasets.

$ hydra-seed-sample --dest ./my_playground
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Stage sample JSONL data.")
    ap.add_argument("--dest", type=Path, required=True, help="target directory")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[3]  # jump out of scripts/…
    sample_dir = repo_root / "data" / "sample"
    assert sample_dir.is_dir(), f"{sample_dir} missing"

    args.dest.mkdir(parents=True, exist_ok=True)
    for f in sample_dir.iterdir():
        shutil.copy2(f, args.dest / f.name)
    print(f"✨  Copied sample set → {args.dest.resolve()}")


if __name__ == "__main__":
    main()
