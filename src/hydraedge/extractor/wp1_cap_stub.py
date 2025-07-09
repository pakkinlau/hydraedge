from __future__ import annotations
from typing import Any, Dict

MAX_LEN = 64
ELLIPSIS = "…"

def cap_and_stub(sentence: str, max_len: int = MAX_LEN) -> Dict[str, Any]:
    """Truncate to ≤ *max_len* tokens and inject SentenceStub when no alpha tokens."""
    toks = sentence.split()
    truncated = toks[:max_len] + ([ELLIPSIS] if len(toks) > max_len else [])
    has_alpha = any(tok.isalpha() for tok in toks)

    result: Dict[str, Any] = {
        "text": " ".join(truncated),
        "stub": None,
    }
    if not has_alpha:
        result["stub"] = {"role": "SENTENCE_STUB", "span": "0:0"}

    return result
