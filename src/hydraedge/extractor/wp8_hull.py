from __future__ import annotations
from collections import defaultdict
from typing import List, Dict, Any

def hullify(tuples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group tuples by eid, then build nested hull dictionaries."""
    by_eid = defaultdict(list)
    for t in tuples:
        by_eid[t["eid"]].append(t)

    def build(eid: str) -> Dict[str, Any]:
        children = [
            build(c_eid) for c_eid in _child_eids(eid, by_eid)  # type: ignore
        ]
        return {"eid": eid, "members": by_eid[eid], "children": children}

    roots = [eid for eid in by_eid if _is_root(eid, by_eid)]
    return [build(r) for r in roots]

def _child_eids(parent: str, groups):
    return [eid for eid in groups if eid.startswith(parent + ".")]

def _is_root(eid: str, groups):
    return not any(eid.startswith(other + ".") for other in groups if other != eid)
