import os, re
from collections import defaultdict
from typing import Dict, List, DefaultDict

import spacy
from pydantic import BaseModel
from transformers import AutoTokenizer, pipeline

# ── one-time model loads ──────────────────────────────────────────
_MODEL  = os.getenv("HYDRA_SRL_MODEL",  "dannashao/bert-base-uncased-finetuned-srl_arg")
_DEVICE = 0 if os.getenv("HYDRA_SRL_DEVICE", "cuda") != "cpu" else -1

_NLP  = spacy.load("en_core_web_sm", disable=["ner"])
_tok  = AutoTokenizer.from_pretrained(_MODEL)
_SRLP = pipeline("token-classification",
                 model=_MODEL,
                 tokenizer=_tok,
                 aggregation_strategy="simple",
                 device=_DEVICE)

_VB_TAG = re.compile(r"^[Vv][BDGNPZ]")        # Penn tags VB, VBD …

def _is_pred(tok) -> bool:
    """Return True when *tok* should be treated as predicate."""
    if tok.pos_ in {"VERB", "AUX"}:                       # std verbs
        return True
    if _VB_TAG.match(tok.tag_):                           # fallback tag
        return True
    if tok.dep_ == "conj" and tok.head.pos_ == "VERB":    # coordinated vb
        return True
    return False


class SRLResult(BaseModel):
    predicates: List[int]
    roles: List[Dict[str, List[int]]]
    doc_id: str
    sent_id: int


def run(doc_id: str, sent_id: int, cap_text: str) -> Dict:
    """
    Parameters
    ----------
    cap_text : str   ≤ 64 tokens (output of wp1)

    Returns
    -------
    SRLResult dict with:
      • predicates: token indices
      • roles     : list-of-dicts aligned to predicates
    """
    doc        = _NLP(cap_text)
    char_spans = [(t.idx, t.idx + len(t.text)) for t in doc]

    predicates: List[int]             = []
    roles_per_pred: List[Dict[str, List[int]]] = []

    for i_pred, tok in enumerate(doc):
        if not _is_pred(tok):
            continue

        # 1) insert marker and run SRL
        tokens          = [t.text for t in doc]
        tokens[i_pred]  = "[V] " + tokens[i_pred]
        marked_sentence = " ".join(tokens)
        spans           = _SRLP(marked_sentence)

        # 2) convert span offsets → token indices
        role_map: DefaultDict[str, List[int]] = defaultdict(list)
        for sp in spans:
            role = sp["entity_group"]
            if role in {"_", "B-V"}:
                continue

            start = sp["start"]
            # account for “[V] ” (4 chars) inserted before predicate
            if sp["start"] > char_spans[i_pred][0]:
                start -= 4

            tok_idx = next(
                (j for j, (a, b) in enumerate(char_spans) if a <= start < b),
                None,
            )
            if tok_idx is not None:
                role_map[role].append(tok_idx)

        predicates.append(i_pred)
        roles_per_pred.append(dict(role_map))

    return SRLResult(
        predicates=predicates,
        roles=roles_per_pred,
        doc_id=doc_id,
        sent_id=sent_id,
    ).model_dump()
