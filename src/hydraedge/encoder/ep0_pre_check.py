# ────────────────────────────────────────────────────────────────────────────────
# HydraEdge · Encoder Stage E0  (implementation + unit tests)
# This single canvas holds TWO files:
#   1. src/hydraedge/encoder/ep0_pre_check.py
#   2. tests/unit/encoder/test_ep0_pre_check.py
# Copy each block verbatim to the indicated path.
# ------------------------------------------------------------------------------

# ==============================================================================
# 1. src/hydraedge/encoder/ep0_pre_check.py
# ==============================================================================
"""Stage E0 – payload pre‑check for encoder chain.

Validates extractor JSON (schema v2.4) **before** any costly encoding work.
Raises :class:`PayloadValidationError` on the first violation so CI fails fast.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

__all__ = [
    "PayloadValidationError",
    "validate",
    "ep0_process",
]

# --- constants -----------------------------------------------------------------
_SCHEMA_VERSION = "2.4"
_REQUIRED_EDGE_KINDS = {"S-P", "P-O", "event-pred", "binder", "meta"}
_CHV_NTYPE = "chv"
_SPO_NTYPE = "spo"
_SENTENCE_STUB = "SentenceStub"

# ------------------------------------------------------------------------------
class PayloadValidationError(RuntimeError):
    """Raised when the extractor payload fails E0 validation."""


# ------------------------------------------------------------------------------
# Public helpers
# ------------------------------------------------------------------------------

def validate(payload: dict, role_registry: Iterable[str]) -> None:  # noqa: C901
    """Validate *payload* in‑place, raising :class:`PayloadValidationError` if bad."""

    def bail(msg: str) -> None:
        raise PayloadValidationError(msg)

    # A. basic shape -----------------------------------------------------------
    if payload.get("version") != _SCHEMA_VERSION:
        bail(f"expected version={_SCHEMA_VERSION}, got {payload.get('version')}")

    nodes: list[dict] = payload.get("nodes", [])
    edges: list[dict] = payload.get("edges", [])
    if not nodes or not edges:
        bail("payload missing nodes or edges array")

    # B. node‑level checks ------------------------------------------------------
    chv_nodes = [n for n in nodes if n.get("ntype") == _CHV_NTYPE]
    if len(chv_nodes) != 1:
        bail("must contain exactly one chv node per sentence")

    spo_nodes = [n for n in nodes if n.get("ntype") == _SPO_NTYPE]
    if not spo_nodes:
        bail("no SPO nodes present – extractor should have injected SentenceStub")

    # alias uniqueness ----------------------------------------------------------
    alias_keys = [n["alias_key"] for n in spo_nodes if "alias_key" in n]
    if len(alias_keys) != len(set(alias_keys)):
        bail("duplicate alias_key detected in sentence")

    # roles known ----------------------------------------------------------------
    valid_roles = set(role_registry)
    unknown_roles = {
        r for n in spo_nodes for r in n.get("roles", []) if r not in valid_roles
    }
    if unknown_roles:
        bail(f"unknown role strings: {sorted(unknown_roles)!r}")

    # C. edge‑level checks ------------------------------------------------------
    for e in edges:
        if e.get("kind") not in _REQUIRED_EDGE_KINDS:
            bail(f"unknown edge kind: {e.get('kind')!r}")

    if not any(e["kind"] == "binder" for e in edges):
        bail("no binder edge linking to chv node found")

    # D. hull integrity ---------------------------------------------------------
    hulls = payload.get("layouts", {}).get("hulls", [])
    spo_id_set = {n["id"] for n in spo_nodes}
    for h in hulls:
        missing = set(h.get("members", [])) - spo_id_set
        if missing:
            bail(f"hull {h['eid']} references unknown members: {missing}")


# ------------------------------------------------------------------------------
# Pipeline adapter
# ------------------------------------------------------------------------------

def ep0_process(payload_json: str | dict, role_registry_path: str | Path) -> dict:
    """Load *payload* (str path or dict), validate, and return it unchanged."""
    if isinstance(payload_json, (str, Path)):
        payload = json.loads(Path(payload_json).read_text("utf‑8"))
    else:
        payload = payload_json

    roles = {line.split("\t", 1)[0] for line in Path(role_registry_path).read_text("utf‑8").splitlines() if line}
    validate(payload, roles)
    return payload
