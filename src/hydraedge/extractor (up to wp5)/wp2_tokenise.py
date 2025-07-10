"""
wp2_tokenise.py  ·  Work-pack 2
──────────────────────────────────────────────────────────────
Input
-----
cap_res : dict from wp1_cap_stub.run()
    • cap          str                 capped sentence
    • offsets      List[(start,end)]   char spans in original text

Output  (all lists share the same length N)
------
{
  "tokens"   : List[str],         # surface form
  "lemmas"   : List[str],         # lower-cased lemma
  "pos"      : List[str],         # coarse POS tag
  "spans"    : List[(int,int)],   # span in capped sentence
  "doc_id"   : str,
  "sent_id"  : int
}
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import spacy
from pydantic import BaseModel

# ══ initialise pipeline once ────────────────────────────────────────────────
_NLP = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "deps"])


class TokeniseResult(BaseModel):
    tokens: List[str]
    lemmas: List[str]
    pos: List[str]
    spans: List[Tuple[int, int]]
    doc_id: str
    sent_id: int


def run(doc_id: str, sent_id: int, cap_text: str) -> Dict:
    """
    Parameters
    ----------
    doc_id, sent_id : provenance
    cap_text        : output of wp1 (≤64 tokens)

    Returns
    -------
    dict-serialisable TokeniseResult
    """
    doc = _NLP(cap_text)

    tokens = [t.text for t in doc]
    lemmas = [t.lemma_.lower() for t in doc]
    pos    = [t.pos_ for t in doc]
    spans  = [(t.idx, t.idx + len(t.text)) for t in doc]

    return TokeniseResult(
        tokens=tokens,
        lemmas=lemmas,
        pos=pos,
        spans=spans,
        doc_id=doc_id,
        sent_id=sent_id,
    ).dict()
