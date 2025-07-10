"""
wp6_roles.py  ·  Role-registry validator
────────────────────────────────────────────────────────────
• Loads the frozen list of admissible SRL labels from roles.tsv.
• Walks over the SRL frames produced by wp4 and the alias-augmented
  span table from wp5.
• Verifies every role string is known; unseen strings are collected
  under `meta.unseen_roles` so CI can fail fast.

Contract
────────
Input  (dict)  – merged pipeline state  after wp5_alias.run()
                required keys:
                  • "frames"      : list[dict] – SRL frames
                  • "doc_id"      : str
                  • "sent_id"     : int
Output (dict)  – adds / replaces two keys:
                  • "roles_ok"       : bool
                  • "meta"["unseen_roles"] : list[str]
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Set

import csv

import logging
_LOG = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#                               Helper functions                              #
# --------------------------------------------------------------------------- #
_CACHE: dict[str, Set[str]] = {}


def _load_role_set(tpath: str | Path) -> Set[str]:
    """Return cached set of admissible role strings."""
    path = str(Path(tpath).expanduser().resolve())
    if path not in _CACHE:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh, delimiter="\t")
            _CACHE[path] = {row[0] for row in reader if row}
        _LOG.info("Loaded %d role labels from %s", len(_CACHE[path]), path)
    return _CACHE[path]


def _collect_roles(frames: List[Dict]) -> List[str]:
    """Extract raw SRL role labels from AllenNLP-style frames."""
    seen: list[str] = []
    for fr in frames:
        for arg in fr.get("arguments", []):
            lab: str = arg.get("label", "")
            if lab:
                seen.append(lab)
    return seen


# --------------------------------------------------------------------------- #
#                                   Runner                                   #
# --------------------------------------------------------------------------- #
def run(state: Dict, *, role_path: str | Path) -> Dict:
    """
    Validate roles against registry and mutate pipeline `state` in-place.

    Args:
        state: accumulator dict passed through pipeline.
        role_path: TSV file with one role per line (first field).

    Returns:
        state (mutated): adds keys "roles_ok" and updates "meta".
    """
    role_set = _load_role_set(role_path)
    frames: List[Dict] = state.get("frames", [])

    found_roles = _collect_roles(frames)
    unseen = sorted({r for r in found_roles if r not in role_set})

    meta = state.setdefault("meta", {})
    meta["unseen_roles"] = unseen
    state["roles_ok"] = not unseen

    if unseen:
        _LOG.warning(
            "Doc %s sent %d – unseen SRL labels: %s",
            state.get("doc_id"), state.get("sent_id"), ", ".join(unseen)
        )

    return state
