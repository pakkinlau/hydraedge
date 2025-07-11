###########################
# File: src/hydraedge/encoder/ep0b_data_typle_check.py
###########################
"""ep0b_data_typle_check
========================
Light‑weight, schema‑aware validator for the *extracted‑JSON* payloads
emitted by the HydraEdge extractor (schema ≥ 2.4).

The module is intentionally **tolerant**: only a minimal, stable core of the
structure is enforced so that research prototypes can iterate on optional
fields without breaking ingestion.

Usage
-----
>>> from hydraedge.encoder.ep0b_data_typle_check import validate_file
>>> ok, errs = validate_file('data/sample/example_payload_batch5c.json')
>>> if not ok:
...     print('\n'.join(errs))
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Tuple

import jsonschema

# ▶ **single source of truth**
from hydraedge.schema import SCHEMA

__all__ = [
    "ValidationError",
    "validate",
    "validate_file",
]


class ValidationError(Exception):
    """Raised when *validate_file* is called with *strict=True* and
    the payload does not conform to the required shape."""


# ---------------------------------------------------------------------------
# Minimal, version‑agnostic contract
# ---------------------------------------------------------------------------
REQUIRED_TOP_LEVEL_KEYS: set[str] = {
    "sentence",   # raw text of the sentence / window
    "nodes",      # list[dict] describing spans / meta / CHV hub
    "edges",      # list[dict] describing typed arcs between nodes
}

NODE_REQUIRED_KEYS: set[str] = {
    "id",        # unique node identifier
    "ntype",     # node category (spo, meta_out, chv, ...)
}

EDGE_REQUIRED_KEYS: set[str] = {
    "source",    # id of head node
    "target",    # id of tail node
    "kind",      # edge type (S-P, P-O, meta, binder, ...)
}

# Optionally recognised — *not* enforced
OPTIONAL_TOP_LEVEL_KEYS = {
    "version", "layouts", "hulls", "metadata", "spans",
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def validate(payload: Dict[str, Any], *, strict: bool = False) -> Tuple[bool, List[str]]:
    """Validate a **parsed JSON object** *payload*.

    Parameters
    ----------
    payload : dict
        The JSON object to validate (already `json.loads`‑ed).
    strict : bool, default False
        If *True*, raise :class:`ValidationError` on any violation.

    Returns
    -------
    ok : bool
        *True* when the payload passes **all** checks.
    errors : list[str]
        Human‑readable messages (empty when *ok* is *True*).
    """
    errors: list[str] = []

    # 1) Top‑level structure --------------------------------------------------
    for k in REQUIRED_TOP_LEVEL_KEYS:
        if k not in payload:
            errors.append(f"Missing top‑level key: '{k}'")

    # 2) Nodes ----------------------------------------------------------------
    nodes = payload.get("nodes", [])
    if not isinstance(nodes, list):
        errors.append("'nodes' must be a list")
    else:
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                errors.append(f"nodes[{i}] is not an object")
                continue
            for nk in NODE_REQUIRED_KEYS:
                if nk not in node:
                    errors.append(f"nodes[{i}] missing key '{nk}'")

    # 3) Edges ----------------------------------------------------------------
    edges = payload.get("edges", [])
    if not isinstance(edges, list):
        errors.append("'edges' must be a list")
    else:
        for j, edge in enumerate(edges):
            if not isinstance(edge, dict):
                errors.append(f"edges[{j}] is not an object")
                continue
            for ek in EDGE_REQUIRED_KEYS:
                if ek not in edge:
                    errors.append(f"edges[{j}] missing key '{ek}'")

    # 4) Referential consistency ---------------------------------------------
    node_ids = {n.get("id") for n in nodes if isinstance(n, dict)}
    for j, edge in enumerate(edges):
        if not isinstance(edge, dict):
            continue  # already reported above
        src, dst = edge.get("source"), edge.get("target")
        if src not in node_ids:
            errors.append(f"edges[{j}] refers to unknown source id '{src}'")
        if dst not in node_ids:
            errors.append(f"edges[{j}] refers to unknown target id '{dst}'")

    # ------------------------------------------------------------------------
    ok = len(errors) == 0
    if strict and not ok:
        raise ValidationError("; ".join(errors))
    return ok, errors


def validate_file(path, strict: bool = True):
    """
    Load JSON at `path`, validate against SCHEMA.
    Returns (ok: bool, errors: list[str]).
    """
    import json
    from pathlib import Path

    txt = Path(path).read_text(encoding="utf-8")
    data = json.loads(txt)
    try:
        validate(data, SCHEMA)
        return True, []
    except Exception as exc:
        # collect human-readable message(s)
        return False, [str(exc)]