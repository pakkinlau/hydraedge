"""
Encode a sentence (or stdin) into a CHV vector and print
• popcount
• first 64 bits• base64 if --b64

$ hydra-encode "I saw a white dog chase the brown cat quickly."
"""
from __future__ import annotations

import argparse
import base64
import sys

import numpy as np

from hydraedge.encoder.chv_encoder import encode_sentence


def main() -> None:
    ap = argparse.ArgumentParser(description="Sentence → CHV encoder")
    ap.add_argument("sentence", nargs="*", help="text to encode (omit to read stdin)")
    ap.add_argument("--b64", action="store_true", help="output base64 blob")
    args = ap.parse_args()

    sentence = " ".join(args.sentence) if args.sentence else sys.stdin.read().strip()
    vec = encode_sentence(sentence)
    pop = int((vec == 1).sum())

    if args.b64:
        packed = np.packbits((vec + 1) // 2).tobytes()
        print(base64.b64encode(packed).decode())
    else:
        bits_preview = "".join("1" if x == 1 else "0" for x in vec[:64])
        print(f"popcount={pop} /{len(vec)}\nfirst64={bits_preview}")


if __name__ == "__main__":
    main()
