from __future__ import annotations
from typing import List, Tuple
from spacy import load

__all__ = ["dependency_arcs"]

# Use the small English model
_NLP = load("en_core_web_sm", disable=["ner"])
_NLP.get_pipe("parser").cfg["beam_width"] = 1   # greedy

def dependency_arcs(text: str) -> List[Tuple[int, int, str]]:
    """
    Returns [(tok_i, head_i, dep_label)] (indices in spaCy doc order).
    """
    doc = _NLP(text)
    return [(tok.i, tok.head.i, tok.dep_) for tok in doc]
