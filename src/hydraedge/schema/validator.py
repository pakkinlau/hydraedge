"""
HydraEdge payload validator · v2.4.1  (2025-07-13)
=================================================

This module augments the **static JSON-Schema** check with **semantic
invariants** that capture the structural rules outlined in the *Batch-6
blueprint* (§ 1.1). Any violation yields a clear error message; CI fails when
`ok is False`.

Usage:

    ok, errs = validate_payload(obj)
    if not ok:
        raise ValueError("Invalid payload:\n" + "\n".join(errs))

New invariants (beyond JSON-Schema):

  S1: `S-P`/`P-O` edges must stay within one event; cross-event links require `event-pred`.
  S2: `event-pred` edges must be `event → spo` and `src.eid ∈ tgt.eid_set`.
  S2b: `subevt` edges must be `spo → spo`.
  S3: `attr` edges must be `attr → spo`.
  S4: `meta` edges must be `meta_out → chv`.
  S5: `binder` edges must be `spo → chv`.
  S6: Exactly one `chv` node per payload.
  S7: Unknown edge kinds are hard errors.
"""

from __future__ import annotations

import json
import jsonschema
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Union

from hydraedge.schema.payload_schema import SCHEMA

# ── constants ─────────────────────────────────────────────────────────────
_ALLOWED_KINDS = {"S-P", "P-O", "attr", "meta", "binder", "event-pred", "subevt"}
_STRIP_RE = re.compile(r"/\*.*?\*/", re.S)

# ── helpers ────────────────────────────────────────────────────────────────
def _strip_js_comments(txt: str) -> str:
    return _STRIP_RE.sub("", txt)

def _nodes_by_id(payload: dict) -> Dict[str, dict]:
    return {n["id"]: n for n in payload.get("nodes", [])}

def _overlap(a: List[str] | None, b: List[str] | None) -> bool:
    return bool(set(a or []).intersection(b or []))

# ── public API ─────────────────────────────────────────────────────────────
PayloadLike = Union[str, bytes, os.PathLike, dict]

def _load_payload(src: PayloadLike) -> dict:
    """
    Accepts:
      - dict → returned as-is
      - Path / os.PathLike → read file, strip JS comments, parse JSON
      - bytes → decode UTF-8, strip comments, parse JSON
      - str → treat as JSON text, strip comments, parse JSON
    """
    if isinstance(src, dict):
        return src

    if isinstance(src, (os.PathLike, Path)):
        text = Path(src).read_text("utf-8")
        return json.loads(_strip_js_comments(text))

    if isinstance(src, bytes):
        raw = src.decode("utf-8")
        return json.loads(_strip_js_comments(raw))

    if isinstance(src, str):
        return json.loads(_strip_js_comments(src))

    raise TypeError("payload must be dict | str | bytes | Path-like")

def validate_payload(payload: PayloadLike) -> Tuple[bool, List[str]]:
    """
    Validate a payload against the JSON schema *and* additional structural invariants.
    Returns (ok, errors). If ok is False, errors contains human-readable messages.
    """
    errs: List[str] = []

    # 1️⃣ JSON-Schema validation
    try:
        obj = _load_payload(payload)
        jsonschema.validate(obj, SCHEMA)
    except json.JSONDecodeError as e:
        return False, [f"JSON-Decode: {e}"]
    except jsonschema.ValidationError as e:
        return False, [f"JSON-Schema: {e.message}"]

    # index nodes
    nodes = _nodes_by_id(obj)

    # S6: exactly one CHV node
    chv_count = sum(1 for n in nodes.values() if n.get("ntype") == "chv")
    if chv_count != 1:
        errs.append("S6: exactly one CHV node required")

    # S1–S5, S7: edge-level invariants
    for ed in obj.get("edges", []):
        kind = ed.get("kind")
        if kind not in _ALLOWED_KINDS:
            errs.append(f"S7: unknown edge kind '{kind}' (edge id={ed.get('id')})")
            continue

        src = nodes.get(ed["source"])
        tgt = nodes.get(ed["target"])
        if src is None or tgt is None:
            errs.append(f"edge references missing node(s): {ed}")
            continue

        s_type = src.get("ntype")
        t_type = tgt.get("ntype")
        s_eid  = src.get("eid")
        s_eids = src.get("eid_set", [])
        t_eids = tgt.get("eid_set", [])

        # S1: S-P / P-O must stay within one event
        if kind in {"S-P", "P-O"} and not _overlap(s_eids, t_eids):
            errs.append(
                f"S1: {kind} edge crosses events – "
                f"{src['id']} ({s_eids}) → {tgt['id']} ({t_eids}); use event-pred instead"
            )

        # S2: only event-pred edges
        elif kind == "event-pred":
            if s_type != "event" or t_type != "spo":
                errs.append(f"S2: event-pred must be event→spo (got {s_type}→{t_type})")
            elif s_eid not in t_eids:
                errs.append(f"S2: event-pred eid mismatch ({s_eid} ∉ {t_eids})")

        # S2b: subevt edges must be spo→spo
        elif kind == "subevt":
            if s_type != "spo" or t_type != "spo":
                errs.append(f"S2b: subevt must be spo→spo (got {s_type}→{t_type})")

        # S3: attr edges
        elif kind == "attr":
            if s_type != "attr" or t_type != "spo":
                errs.append(f"S3: attr edge must be attr→spo (got {s_type}→{t_type})")

        # S4: meta edges
        elif kind == "meta":
            if s_type != "meta_out" or t_type != "chv":
                errs.append("S4: meta edges must be meta_out→chv")

        # S5: binder edges
        elif kind == "binder":
            if s_type != "spo" or t_type != "chv":
                errs.append("S5: binder edges must be spo→chv")

    return (not errs), errs


__all__ = ["validate_payload"]
