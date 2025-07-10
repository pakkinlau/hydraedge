#!/usr/bin/env python3
"""
wp8_hull.py  ·  WP-8  —  Event-Hull Construction
─────────────────────────────────────────────────────────────────────────────
Groups raw tuples (WP-7) into hierarchical “hulls” keyed by **eid** and
detects parent–child links when a tuple’s span re-appears as an ARG-role
inside another hull.

A hull is a plain dict:

    {
      "eid"     : str,                 # entity / event id
      "members" : [ tuple_obj, … ],    # shallow copies
      "children": [ child_hull, … ]    # recursive
    }

Public API
──────────
• `hullify(tuples: List[dict]) -> List[dict]`
    Pure function used by the unit-tests.

• `HullStage` — Pipeline stage that writes the hull list to
    `ctx.data["hulls"]` and diagnostics to `ctx.debug["hull"]`.

No external dependencies.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List

from hydraedge.extractor.base import Ctx, PipelineStage, register

__all__ = ["HullStage", "hullify"]

logger = logging.getLogger(__name__)


# ╭──────────────────────────────────────────────────────────────╮
# │ Pure helper – used in tests & stage                          │
# ╰──────────────────────────────────────────────────────────────╯
def hullify(tuples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build a **nested** hull tree from a flat list of tuple-dicts.

    The algorithm:

    1.  Group tuples that share the same `eid`.
    2.  Build initial top-level hull list.
    3.  Detect parent/child relations:
        if a member’s *span text* (case-insensitive) re-appears as ARGn in
        another hull, treat the former hull as a child of the latter.
    4.  Return the list of **root** hulls (deterministic order = first seen).

    The function performs *no* in-place mutations on the input tuples.
    """
    # ── 1 ▸ group by EID ─────────────────────────────────────────
    by_eid: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for tup in tuples:
        by_eid[str(tup["eid"])].append(tup)

    hulls: List[Dict[str, Any]] = [
        {"eid": eid, "members": members, "children": []}
        for eid, members in by_eid.items()
    ]

    # ── 2 ▸ span-to-EID lookup for parent/child detection ───────
    span2eid: Dict[str, str] = {}
    for h in hulls:
        for m in h["members"]:
            span2eid[m["span"].lower()] = h["eid"]

    parent_of: Dict[str, str] = {}  # child_eid → parent_eid
    for h in hulls:
        for m in h["members"]:
            child_eid = span2eid.get(m["span"].lower())
            if child_eid and child_eid != h["eid"]:
                parent_of[child_eid] = h["eid"]

    # ── 3 ▸ assemble the tree ───────────────────────────────────
    id2hull = {h["eid"]: h for h in hulls}
    roots: List[Dict[str, Any]] = []
    for h in hulls:
        pid = parent_of.get(h["eid"])
        if pid:
            id2hull[pid]["children"].append(h)
        else:
            roots.append(h)

    return roots


# ╭──────────────────────────────────────────────────────────────╮
# │ Pipeline stage                                               │
# ╰──────────────────────────────────────────────────────────────╯
@register
class HullStage(PipelineStage):
    """WP-8 — wrap `hullify()` into the pipeline framework."""

    name = "hull"
    requires = ["tuples"]
    provides = ["hulls"]

    # This stage is stateless; constructor only calls super().
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    # Core runner
    def run(self, ctx: Ctx) -> None:  # noqa: D401
        tuples: List[Dict[str, Any]] = ctx.data["tuples"]
        roots = hullify(tuples)

        ctx.data["hulls"] = roots
        ctx.debug[self.name] = {
            "total_hulls": len(tuples),
            "root_count": len(roots),
            "nested": sum(len(h["children"]) for h in roots),
        }
        logger.debug(
            "WP-8 built %d root hulls (%d tuples total)",
            len(roots),
            len(tuples),
        )
