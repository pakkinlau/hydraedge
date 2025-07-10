"""
wp1_cap_stub.py  ·  Work-pack 1
─────────────────────────────────────────────────────────────
• Truncate the raw sentence to ≤ CAP_LEN tokens (SpaCy).
• Record original ⇢ capped offset map.
• Emit stub tuple when spaCy finds no VERB or NOUN/PROPN.

Outputs (dict)
--------------
cap: str               # possibly truncated sentence
offsets: List[tuple]   # (orig_start, orig_end) for each token kept
inject_stub: bool      # True ⇢ downstream rule-map must add SentenceStub
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import spacy
from pydantic import BaseModel

# ---------- Load once ----------
_NLP = spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])
_CAP_LEN = 64  # overridden by config/extractor.yaml if present


class CapStubResult(BaseModel):
    cap: str
    offsets: List[Tuple[int, int]]
    inject_stub: bool
    meta: Dict[str, str] = {}


def _need_stub(doc: "spacy.tokens.Doc") -> bool:
    """Heuristic: no verb ⇒ no predicate; or no noun/proper ⇒ no subject/object."""
    has_verb = any(t.pos_ in {"VERB", "AUX"} for t in doc)
    has_noun = any(t.pos_ in {"NOUN", "PROPN"} for t in doc)
    return not (has_verb and has_noun)


def run(doc_id: str, sent_id: int, text: str, cap_len: int = _CAP_LEN) -> Dict:
    """
    HydraEdge WP interface.

    Parameters
    ----------
    doc_id, sent_id : provenance
    text            : raw sentence
    cap_len         : hard token cap (default 64)

    Returns
    -------
    dict compatible with CapStubResult
    """
    doc = _NLP(text)
    keep = doc[:cap_len]
    cap_text = keep.text if len(doc) > cap_len else text

    offsets = [(tok.idx, tok.idx + len(tok.text)) for tok in keep]
    inject_stub = _need_stub(doc)

    return CapStubResult(
        cap=cap_text,
        offsets=offsets,
        inject_stub=inject_stub,
        meta={"doc_id": doc_id, "sent_id": str(sent_id)},
    ).dict()
