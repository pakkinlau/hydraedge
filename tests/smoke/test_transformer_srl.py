#!/usr/bin/env python3
"""
test_single_sentence_srl.py — GPU-first SRL smoke-test
Python 3.12 • no trust_remote_code • no weight warnings
"""
from __future__ import annotations
import re, sys
from typing import List, Dict

# ── 0 ▸ Config ────────────────────────────────────────────────────
DEVICE = "cuda:0" if (sys.argv.count("--cpu") == 0) else "cpu"   # GPU by default
MODEL  = "dannashao/bert-base-uncased-finetuned-srl_arg"
SENTENCE = "I saw a white dog chase the brown cat quickly in the backyard."

# ── 1 ▸ Protobuf alias (legacy libs may need it) ──────────────────
import google.protobuf as _pb; sys.modules.setdefault("protobuf", _pb)

# ── 2 ▸ Load SRL pipeline (ready-made HF head) ────────────────────
from transformers import AutoTokenizer, pipeline
tok = AutoTokenizer.from_pretrained(MODEL)
srl = pipeline(
    task="token-classification",
    model=MODEL,
    tokenizer=tok,
    aggregation_strategy="simple",
    device=DEVICE,
)

# ── 3 ▸ Minimal POS tagger (spaCy) to find verbs ──────────────────
import spacy; _nlp = spacy.load("en_core_web_sm")
_VB = re.compile(r"^[Vv][BDGNPZ]")          # Penn verb tags

def verb_indices(doc) -> List[int]:
    return [i for i, tok in enumerate(doc) if _VB.match(tok.tag_)]

# ── 4 ▸ Extract roles for one sentence ────────────────────────────
def extract(sentence: str) -> List[Dict]:
    doc = _nlp(sentence)
    out: List[Dict] = []
    for i_pred in verb_indices(doc):
        tokens = [t.text for t in doc]
        tokens[i_pred] = "[V] " + tokens[i_pred]      # insert SRL marker
        spans = srl(" ".join(tokens))
        for sp in spans:
            role = sp["entity_group"]
            if role in {"_", "B-V"}:
                continue
            out.append({
                "predicate": doc[i_pred].lemma_,
                "role"     : role,
                "span"     : sp["word"],
            })
    return out

# ── 5 ▸ Run & display ─────────────────────────────────────────────
results = extract(SENTENCE)
assert results, "No arguments extracted — check spaCy model & SRL checkpoint."
from pprint import pprint
pprint(results, compact=True, width=100)
print(f"\n✓ SRL completed on {DEVICE}.  {len(results)} argument spans found.")

""" 
Output:

[{'predicate': 'see', 'role': 'ARG0', 'span': 'i'},
 {'predicate': 'see', 'role': 'ARG1', 'span': 'chase'}]
"""