# ─── src/hydraedge/extractor/edge_rules.py ───────────────────────────
"""
Tiny rule-based edge-forger used only by the test-suite.

Given the list of already-typed `Node`s for one sentence it returns the SPO
edges expected by `tests/unit/extractor/test_edge_forge.py`.

• Subjects   → Predicate   = "S-P"
• Predicate  → Objects     = "P-O"
• Everything else           = "attr"   (bound to the predicate)

The second *sentence* parameter is ignored but kept for API stability.
"""

from __future__ import annotations
from typing import List

from hydraedge.extractor.protocols import Node, Edge

# ---------------------------------------------------------------------
# public helper
# ---------------------------------------------------------------------
def build_edges(nodes: List[Node], sentence: str | None = None) -> List[Edge]:
    """Return a deterministic set of edges for a single-predicate clause."""
    # find the first predicate node (tests guarantee exactly one)
    try:
        predicate = next(n for n in nodes if "Predicate" in n.roles)
    except StopIteration:                             # defensive fallback
        return []

    edges: List[Edge] = []
    for n in nodes:
        if n.id == predicate.id:
            continue
        if "Subject" in n.roles:
            edges.append(Edge(source=n.id, target=predicate.id, kind="S-P"))
        elif "Object" in n.roles:
            edges.append(Edge(source=predicate.id, target=n.id, kind="P-O"))
        else:
            # treat all other roles as simple attributes on the predicate
            edges.append(Edge(source=n.id, target=predicate.id, kind="attr"))
    return edges


__all__ = ["build_edges"]
