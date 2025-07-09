#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wp3b_vfinder.py  ·  Fast verb-finder pre-pass
----------------------------------------------
Detects if a sentence has ≥1 main verb; if none, downstream SRL is skipped.

Requires spaCy ≥3.5.
"""

from __future__ import annotations
from typing import Dict
import spacy

# Initialize minimal spaCy pipeline once
_NLP = spacy.blank("en")
_NLP.add_pipe("tok2vec")
_NLP.add_pipe("tagger")


def has_verb(sentence: str) -> bool:
    """
    Return True iff sentence contains a standalone VERB or AUX token.
    Excludes auxiliaries that are dependents of other verbs.
    """
    doc = _NLP(sentence)
    for tok in doc:
        if tok.pos_ in {"VERB", "AUX"} and tok.head == tok:
            return True
    return False


def run(doc_id: str, sent_id: int, text: str) -> Dict:
    """
    HydraEdge extractor interface.
    Returns:
        {
          "doc_id":   doc_id,
          "sent_id":  sent_id,
          "skip_srl": True if no verb found (bypass wp4_srl)
        }
    """
    return {"doc_id": doc_id, "sent_id": sent_id, "skip_srl": not has_verb(text)}
