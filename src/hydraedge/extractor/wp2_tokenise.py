from __future__ import annotations
import random, numpy as np
from spacy import load
from typing import List, Tuple

__all__ = ["tokenise_pos"]

# Determinism
random.seed(42)
np.random.seed(42)

# Use the small English model (guaranteed installed)
_NLP = load("en_core_web_sm", disable=["ner"])

def tokenise_pos(text: str) -> List[Tuple[str, str, int]]:
    """
    Returns [(token, POS, char_offset)] for *text*.
    Greedy parse ⇒ deterministic.
    """
    doc = _NLP(text)
    return [(tok.text, tok.pos_, tok.idx) for tok in doc]
