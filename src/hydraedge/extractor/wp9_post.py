from __future__ import annotations
from typing import List, Dict, Any
import spacy

__all__ = ["merge_spans", "tag_tense"]

_NLP = spacy.blank("en")

def merge_spans(tuples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collapse duplicate alias spans inside one sentence."""
    seen = set()
    out = []
    for t in tuples:
        if t["span"] in seen:
            continue
        seen.add(t["span"])
        out.append(t)
    return out

def tag_tense(word: str) -> str | None:
    """Return spaCy morph tense tag or None."""
    doc = _NLP(word)
    tok = doc[0]
    return tok.morph.get("Tense")[0] if tok.morph.get("Tense") else None
