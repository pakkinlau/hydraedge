# src/hydraedge/extractor/wp5_alias.py

from __future__ import annotations
import pycountry
from typing import Dict, Any, List, Optional, Tuple


def _normalize_country(tok: str) -> Optional[Tuple[str, str]]:
    """Try ISO alpha-2 code or common name lookup; return (key, value) if found."""
    t = tok.strip().upper()
    # 1) Exact alpha_2 code
    country = pycountry.countries.get(alpha_2=t)
    if country:
        name = country.name
        key = name.lower().replace(" ", "_")
        return key, name
    # 2) Lookup by name or common alias
    try:
        country = pycountry.countries.lookup(tok)
        name = country.name
        key = name.lower().replace(" ", "_")
        return key, name
    except (LookupError, AttributeError):
        return None


def run(
    doc_id: str,
    sent_id: int,
    tok_res: Dict[str, Any],
    srl_res: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Alias stage: maps each token to a canonical key (e.g. country codes → 'united_states'),
    or falls back to the lowercase lemma or token text. Returns a dict with:
      {
        "doc_id": ...,  # same as input
        "sent_id": ...,  # same as input
        "alias_keys": [...],   # one per token
        "alias_values": [...], # corresponding values
      }
    """
    tokens: List[str] = tok_res["tokens"]
    lemmas:  List[str] = tok_res.get("lemmas", tokens)

    alias_keys:   List[str] = []
    alias_values: List[str] = []

    for tok, lem in zip(tokens, lemmas):
        norm = _normalize_country(tok)
        if norm:
            key, val = norm
        else:
            # if lemma present, use it; otherwise fallback to token
            if lem:
                key, val = lem.lower(), lem
            else:
                key, val = tok.lower(), tok
        alias_keys.append(key)
        alias_values.append(val)

    return {
        "doc_id":       doc_id,
        "sent_id":      sent_id,
        "alias_keys":   alias_keys,
        "alias_values": alias_values,
    }
