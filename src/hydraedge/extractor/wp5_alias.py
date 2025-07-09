# src/hydraedge/extractor/wp5_alias.py

from __future__ import annotations
from typing import Dict
import pathlib, csv
from sentence_transformers import SentenceTransformer, util
import numpy as np

__all__ = ["AliasResolver"]

_MODEL = SentenceTransformer("all-MiniLM-L6-v2")  # cached globally


class AliasResolver:
    """
    Exact-match gazetteer → MiniLM similarity fallback (≥0.8).
    If the TSV is empty (no entries), resolve() simply returns span.lower().
    """
    def __init__(self, tsv_path: str | pathlib.Path):
        self.gaz: Dict[str, str] = {}
        self.embs: Dict[str, np.ndarray] = {}
        # Load every line as: key<TAB>alias1<TAB>alias2...
        with open(tsv_path, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh, delimiter="\t")
            for row in reader:
                if not row:
                    continue
                key, *aliases = row
                # map each alias → key
                for a in aliases:
                    self.gaz[a.lower()] = key
                # pre-encode the canonical key
                self.embs[key] = _MODEL.encode(key, normalize_embeddings=True)

    def resolve(self, span: str) -> str:
        s = span.lower().strip()
        # 1) exact match
        if s in self.gaz:
            return self.gaz[s]
        # 2) if nothing in emb dictionary, skip nearest-neighbor
        if not self.embs:
            return s
        # 3) nearest-key fallback
        emb = _MODEL.encode(span, normalize_embeddings=True)
        best, score = max(
            ((k, util.cos_sim(emb, v).item()) for k, v in self.embs.items()),
            key=lambda kv: kv[1],
        )
        return best if score >= 0.80 else s
