#!/usr/bin/env python3
"""
test_single_sentence_srl.py — GPU-first SRL smoke-test
Python 3.12 • no trust_remote_code • no weight warnings
"""
# tests/smoke/test_transformer_srl.py
from __future__ import annotations
import re, sys
from typing import List, Dict
import google.protobuf as _pb; sys.modules.setdefault("protobuf", _pb)

import spacy
from transformers import AutoTokenizer, pipeline

DEVICE = "cuda:0" if "--cpu" not in sys.argv else "cpu"
MODEL = "dannashao/bert-base-uncased-finetuned-srl_arg"
SENTENCE = "I saw a white dog chase the brown cat quickly in the backyard."

_VB = re.compile(r"^[Vv][BDGNPZ]")          # Penn verb tags
tok = AutoTokenizer.from_pretrained(MODEL)
srl = pipeline(
    task="token-classification",
    model=MODEL,
    tokenizer=tok,
    aggregation_strategy="simple",
    device=DEVICE,
)
_nlp = spacy.load("en_core_web_sm")


def _verb_indices(doc) -> List[int]:
    return [i for i, tok in enumerate(doc) if _VB.match(tok.tag_)]


def extract(sentence: str) -> List[Dict]:
    doc = _nlp(sentence)
    out = []
    for i_pred in _verb_indices(doc):
        tokens = [t.text for t in doc]
        tokens[i_pred] = "[V] " + tokens[i_pred]
        spans = srl(" ".join(tokens))
        out.extend(
            {
                "predicate": doc[i_pred].lemma_,
                "role": sp["entity_group"],
                "span": sp["word"],
            }
            for sp in spans
            if sp["entity_group"] not in {"_", "B-V"}
        )
    return out


# ---------- PyTest entry point ----------
def test_single_sentence_srl():
    """Smoke-test that at least one semantic role is extracted."""
    results = extract(SENTENCE)
    assert results, "No arguments extracted — check spaCy model & SRL checkpoint."


""" 
Output:

[{'predicate': 'see', 'role': 'ARG0', 'span': 'i'},
 {'predicate': 'see', 'role': 'ARG1', 'span': 'chase'}]
"""