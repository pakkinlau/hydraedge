# src/hydraedge/extractor/wp5_alias.py

from __future__ import annotations
from typing import Dict
import pathlib, csv
from sentence_transformers import SentenceTransformer, util
import numpy as np

__all__ = ["AliasResolver"]

_MODEL = SentenceTransformer("all-MiniLM-L6-v2")  # cached in RAM

class AliasResolver:
    """
    Exact-match gazetteer → MiniLM similarity search fallback (≥ 0.8).
    If the gazetteer is empty, falls back immediately to span.lower().
    """
    def __init__(self, tsv_path: str | pathlib.Path):
        self.gaz: Dict[str, str] = {}
        self.embs: Dict[str, np.ndarray] = {}
        with open(tsv_path, newline="", encoding="utf-8") as fh:
            for key, *aliases in csv.reader(fh, delimiter="\t"):
                for a in aliases:
                    self.gaz[a.lower()] = key
                # encode the canonical key itself
                self.embs[key] = _MODEL.encode(key, normalize_embeddings=True)

    def resolve(self, span: str) -> str:
        s = span.lower()
        # exact gazetteer match
        if s in self.gaz:
            return self.gaz[s]
        # if no embeddings loaded, skip similarity
        if not self.embs:
            return s
        # fallback: find closest canonical key
        emb = _MODEL.encode(span, normalize_embeddings=True)
        best, score = max(
            ((k, util.cos_sim(emb, v).item()) for k, v in self.embs.items()),
            key=lambda kv: kv[1],
        )
        return best if score >= 0.80 else s
