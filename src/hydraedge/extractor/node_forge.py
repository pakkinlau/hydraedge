from __future__ import annotations
from typing import List, Tuple, Set
from .protocols import Node


def forge_nodes(tuples: List[Tuple[str, str]],
                sentence: str,
                eid: str = "e1") -> List[Node]:
    """
    Converts (role, filler) pairs → `Node` objects.

    * everything goes into the **SPO tier** (“ntype” = "spo")
    * `alias_key` = lower-cased filler
    * character span is first `.find()` match (-1 if absent)
    """
    out: List[Node] = []
    seen: Set[str] = set()

    for role, tok in tuples:
        nid = f"spo:{tok}@{eid}"
        if nid in seen:
            continue
        seen.add(nid)

        c0 = sentence.lower().find(tok.lower())
        c1 = c0 + len(tok) if c0 != -1 else -1

        out.append(
            Node(
                id=nid,
                filler=tok,
                alias_key=tok.lower(),
                roles=[role],
                eid_set=[eid],
                ntype="spo",
                char_start=c0,
                char_end=c1,
            )
        )
    return out
