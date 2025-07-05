# ─── hydraedge.extractor.protocols ──────────────────────────────────────────────
"""
🔑  Core data contracts for the extraction pipeline.
Keep this file tiny and *extremely* stable – most downstream code should only
import from here (not from the concrete extractor implementation).

All classes are frozen NamedTuples ⇒
  • hashable / usable as dict keys
  • super-cheap to create
  • immutable → safer to pass around
If some stage really needs mutability, copy into a `dict(node._asdict())`
or create a light dataclass wrapper locally.
"""

from __future__ import annotations
from typing import NamedTuple, Literal, TypedDict, List, Dict

# ────────────────────────────────────────────────────────────────────────────────
Role = Literal[
    "Subject", "Predicate", "Object",
    "IndirectObject", "Attr",
    "Tense", "VerbClass", "Type",
    "Source", "Date", "Venue",
    "Event",        # reserved (not always used)
    "CHV"           # the anchor node
]

EdgeKind = Literal["S-P", "P-O", "attr", "subevt", "meta", "binder"]


class Node(NamedTuple):
    id: str                 # e.g. "spo:cat@e2"
    filler: str             # surface string or canonical form
    alias_key: str          # lower-cased lookup key (can be "")
    roles: List[Role]       # primary role in [0]; extras allowed
    eid_set: List[str]      # events this node belongs to (e#, ...)
    ntype: Literal["spo", "attr", "meta_out", "chv"]
    char_start: int         # –1 if synthetic
    char_end: int           # –1 if synthetic


class Edge(NamedTuple):
    source: str
    target: str
    kind: EdgeKind


class Layouts(TypedDict, total=False):
    """Optional visual/layout hints."""
    hulls: List[Dict]       # free-form JSON blob – visualiser specific


class ExtractionOutput(NamedTuple):
    sentence: str
    nodes: List[Node]
    edges: List[Edge]
    layouts: Layouts
# ────────────────────────────────────────────────────────────────────────────────

# tag → Role mapping (PropBank v1)
RULES = {
    "B-ARG0": "Subject",
    "B-ARG1": "Object",
    "B-ARG2": "Object",
    "B-ARGM-LOC": "IndirectObject",
    "B-ARGM-MNR": "Attr",
    # …extend as we support more frames
}
def map_tag(tag: str) -> Role | None:
    return RULES.get(tag)

__all__ = [
    "Role", "EdgeKind",
    "Node", "Edge",
    "Layouts", "ExtractionOutput", "RULES", "map_tag",
]
