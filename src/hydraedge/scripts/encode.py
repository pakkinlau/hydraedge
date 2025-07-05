"""
CLI: hydra-encode — encode a JSONL corpus into CHV vectors
---------------------------------------------------------

Examples
--------
# encode an entire corpus
hydra-encode \
   --model chv:default \
   --in  data/sample/tiny_corpus.jsonl \
   --out vectors.npy

# encode + write separate id list
hydra-encode -i my.jsonl -o my.npy -d ids.txt
"""
from __future__ import annotations
import argparse, json, sys
import numpy as np
from pathlib import Path
from hydraedge.encoder.chv_encoder import ChvEncoder           # <- already exists


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="hydra-encode")
    p.add_argument("-i", "--in", dest="inp", required=True,
                   help="Input JSONL file (schema ≥ 2.4)")
    p.add_argument("-o", "--out", required=True,
                   help="Output .npy file (float32 vectors)")
    p.add_argument("-d", "--ids-out", default=None,
                   help="Optional txt file with one doc-id per line")
    p.add_argument("--model", default="chv:default",
                   help="Encoder name (future-proof – unused for now)")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    inp  = Path(args.inp)
    out  = Path(args.out).with_suffix(".npy")
    ids_out = Path(args.ids_out) if args.ids_out else None

    enc = ChvEncoder()                           # 4096-d default

    vecs, ids = [], []
    with inp.open() as fh:
        for line in fh:
            rec = json.loads(line)
            vecs.append(enc.encode_json(rec))
            ids.append(rec.get("id") or rec.get("_id") or str(len(ids)))

    vecs_np = np.stack(vecs).astype("float32")
    out.parent.mkdir(parents=True, exist_ok=True)
    np.save(out, vecs_np)
    if ids_out:
        ids_out.parent.mkdir(parents=True, exist_ok=True)
        ids_out.write_text("\n".join(map(str, ids)))

    print(f"✅  wrote {len(vecs_np)} × {vecs_np.shape[1]} → {out}")
    if ids_out:
        print(f"    ids → {ids_out}")


if __name__ == "__main__":
    main()
