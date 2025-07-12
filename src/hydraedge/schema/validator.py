"""
HydraEdge payload validator · v2.5.0  (2025-07-14)
=================================================

Runs the static **JSON-Schema** check *plus* semantic invariants:

  S1  `S-P` / `P-O` edges may not cross event-IDs.
  S2  `event-pred` / `subevt` edges must be **event → spo** and share an eid.
  S3  `attr`  edges must be **attr → spo**.
  S4  `meta`  edges must be **meta_out → chv**.
  S5  `binder` edges must be **spo → chv**.
  S6  Exactly one `chv` node per payload.
  S7  Unknown edge kinds are hard errors.
  S8  Every node must be reachable (undirected) from that single CHV node.

Usage
-----
    from hydraedge.schema.validator import validate_payload

    ok, errs = validate_payload(payload_or_path_or_json)
    if not ok:
        raise ValueError("Invalid payload:\n" + "\n".join(errs))
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Union

import jsonschema
from hydraedge.schema.payload_schema import SCHEMA

# ── constants ────────────────────────────────────────────────────────────

_ALLOWED_KINDS = {
    "S-P", "P-O", "attr", "meta", "binder", "event-pred", "subevt",
}
_STRIP_RE = re.compile(r"/\*.*?\*/", re.S)  # naïve “/* … */” remover

# ── helpers ──────────────────────────────────────────────────────────────

def _strip_js_comments(txt: str) -> str:
    """Remove C/JS-style block comments so test fixtures may embed JSON."""
    return _STRIP_RE.sub("", txt)

def _nodes_by_id(payload: dict) -> Dict[str, dict]:
    return {n["id"]: n for n in payload.get("nodes", [])}

def _overlap(a: List[str] | None, b: List[str] | None) -> bool:
    return bool(set(a or []).intersection(b or []))

def _reachable_from_chv(nodes: Dict[str, dict], edges: List[dict]) -> bool:
    """
    True iff every node is (undirected)-connected to the single CHV.
    """
    # build adjacency
    adj: Dict[str, set[str]] = {nid: set() for nid in nodes}
    for e in edges:
        s, t = e["source"], e["target"]
        adj[s].add(t)
        adj[t].add(s)

    # locate the CHV
    chv_nodes = [nid for nid, n in nodes.items() if n.get("ntype") == "chv"]
    if len(chv_nodes) != 1:
        return False
    root = chv_nodes[0]

    # BFS
    seen = {root}
    stack = [root]
    while stack:
        cur = stack.pop()
        for nbr in adj[cur]:
            if nbr not in seen:
                seen.add(nbr)
                stack.append(nbr)

    return len(seen) == len(nodes)

# ── public API ────────────────────────────────────────────────────────────

PayloadLike = Union[str, bytes, os.PathLike, dict]

def _load_payload(src: PayloadLike) -> dict:
    """
    Accepts:
      - dict → returned as-is
      - Path / os.PathLike → read file (strips /*…*/ comments)
      - bytes → decode UTF-8 then parse
      - str → if JSON-like (starts with { or [) parse directly, else treat as path
    """
    if isinstance(src, dict):
        return src

    # Path-like
    if isinstance(src, (os.PathLike, Path)):
        text = Path(src).read_text("utf-8")
        return json.loads(_strip_js_comments(text))

    # bytes → decode
    if isinstance(src, bytes):
        raw = src.decode("utf-8")
        return json.loads(_strip_js_comments(raw))

    # str → JSON text vs filesystem path
    if isinstance(src, str):
        s = src.strip()
        if s.startswith("{") or s.startswith("["):
            return json.loads(_strip_js_comments(src))
        text = Path(src).read_text("utf-8")
        return json.loads(_strip_js_comments(text))

    raise TypeError("payload must be dict | str | bytes | Path-like")

def validate_payload(payload: PayloadLike) -> Tuple[bool, List[str]]:
    """
    Validate against JSON-Schema *and* semantic invariants.
    Returns (ok, [error strings…]).
    """
    errs: List[str] = []

    # 1️⃣ JSON-Schema check
    try:
        obj = _load_payload(payload)
        jsonschema.validate(obj, SCHEMA)
    except json.JSONDecodeError as e:
        return False, [f"JSON-Decode: {e}"]
    except jsonschema.ValidationError as e:
        return False, [f"JSON-Schema: {e.message}"]

    # index nodes
    nodes = _nodes_by_id(obj)

    # S6 – exactly one CHV node
    chv_count = sum(1 for n in nodes.values() if n.get("ntype") == "chv")
    if chv_count != 1:
        errs.append("S6: exactly one CHV node required")

    # S1–S5, S7 – per-edge invariants
    for ed in obj.get("edges", []):
        kind = ed.get("kind")
        if kind not in _ALLOWED_KINDS:
            errs.append(f"S7: unknown edge kind '{kind}' ({ed})")
            continue

        src = nodes.get(ed["source"])
        tgt = nodes.get(ed["target"])
        if src is None or tgt is None:
            errs.append(f"edge references missing node(s): {ed}")
            continue

        s_type, t_type = src.get("ntype"), tgt.get("ntype")
        s_eids, t_eids = src.get("eid_set", []), tgt.get("eid_set", [])
        s_eid = src.get("eid")  # only event nodes carry a single eid

        # S1 – S-P / P-O must stay within one event
        if kind in {"S-P", "P-O"} and not _overlap(s_eids, t_eids):
            errs.append(
                f"S1: {kind} crosses events {s_eids}↔{t_eids}; use event-pred instead"
            )

        # S2 – event-pred / subevt must be event→spo with matching eid
        # S2a – event-pred  (event → spo, eid containment)
        elif kind == "event-pred":
            if s_type != "event" or t_type != "spo":
                errs.append(f"S2: event-pred must be event→spo (got {s_type}→{t_type})")
            elif s_eid not in t_eids:
                errs.append(f"S2: event-pred eid mismatch ({s_eid} ∉ {t_eids})")

        # S2b – subevt  (predicate→predicate, no eid check)
        elif kind == "subevt" and not (s_type == t_type == "spo"):
            errs.append(f"S2: subevt must be spo→spo (got {s_type}→{t_type})")


        # S3 – attr edges
        elif kind == "attr" and not (s_type == "attr" and t_type == "spo"):
            errs.append(f"S3: attr edge must be attr→spo (got {s_type}→{t_type})")

        # S4 – meta edges
        elif kind == "meta" and not (s_type == "meta_out" and t_type == "chv"):
            errs.append("S4: meta edges must be meta_out→chv")

        # S5 – binder edges
        elif kind == "binder" and not (s_type == "spo" and t_type == "chv"):
            errs.append("S5: binder edges must be spo→chv")

    # S8 – global connectivity (only if no earlier errors)
    if not errs and not _reachable_from_chv(nodes, obj.get("edges", [])):
        errs.append(
            "S8: graph has ≥2 disconnected components; every node must connect to CHV"
        )

    return (not errs), errs


__all__ = ["validate_payload"]
