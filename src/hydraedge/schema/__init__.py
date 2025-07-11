"""Shared JSON-Schema for HydraEdge sentence-level payloads  (v 2.4-minimal).

The goal is to guarantee a *sound outer shape* while staying tolerant to
forward-compatible additions.  Anything we do **not** explicitly care about is
allowed via `additionalProperties: true`.
"""
from __future__ import annotations

SCHEMA: dict = {
    "type": "object",
    "required": ["nodes", "edges"],
    "additionalProperties": True,
    "properties": {
        # ───────────────────────────────────────────────────────── nodes ──
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "ntype"],
                "additionalProperties": True,  # forward-compatible
            },
        },
        # ───────────────────────────────────────────────────────── edges ──
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source", "target", "kind"],
                "additionalProperties": True,
                "properties": {
                    "source": {"type": ["string", "integer"]},
                    "target": {"type": ["string", "integer"]},
                    "kind": {"type": "string"},
                },
            },
        },
        # ───────────────────────────── optional helpers (layout, text) ──
        "layouts": {"type": "object", "additionalProperties": True},
        "sentence": {"type": "string"},
    },
}
