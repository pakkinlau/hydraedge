"""
wp3_dependency.py  ·  Work-pack 3
──────────────────────────────────────────────────────────────────
Input
-----
cap_text : str                 (from wp1)
tok_res  : dict                (from wp2_tokenise)  – tokens, spans …

Output
------
{
  "heads"   : List[int],   # head index or -1 for root
  "deps"    : List[str],   # dependency labels
  "root"    : int,         # index of syntactic root
  "doc_id"  : str,
  "sent_id" : int
}
"""

from __future__ import annotations

from typing import Dict, List

import spacy
from pydantic import BaseModel

# — load parser once —
_PARSER = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])


class DepResult(BaseModel):
    heads: List[int]
    deps: List[str]
    root: int
    doc_id: str
    sent_id: int


def run(doc_id: str, sent_id: int, cap_text: str) -> Dict:
    """
    Parameters
    ----------
    doc_id, sent_id : provenance
    cap_text        : capped sentence (≤64 tokens)

    Returns
    -------
    dict (DepResult)
    """
    doc = _PARSER(cap_text)

    heads = []
    deps  = []
    root  = -1
    for i, tok in enumerate(doc):
        heads.append(tok.head.i if tok.head != tok else -1)
        deps.append(tok.dep_)
        if tok.head == tok:
            root = i

    return DepResult(
        heads=heads,
        deps=deps,
        root=root,
        doc_id=doc_id,
        sent_id=sent_id,
    ).dict()
