#!/usr/bin/env python3
"""
HydraEdge Payload Schema Validator

Validates extracted JSON payloads against the Nested-event CHV graph schema (v2.4).
Strips JavaScript-style /* ... */ comments, patches the schema to accept any extra enum values
found in the data (e.g., new edge kinds or node types), and returns all structural errors.
"""
import json
import re
from pathlib import Path
from typing import Tuple, List, Dict, Any

import jsonschema
from jsonschema import Draft202012Validator

# ────────────────────────────────────────────────────────────────────────────
# 1 · Core SCHEMA definition for Nested-event CHV graph (v2.4)
# ────────────────────────────────────────────────────────────────────────────
SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Nested-event CHV graph",
    "type": "object",
    "required": ["version", "sentence", "nodes", "edges"],
    "properties": {
        "version":  {"type": "string"},
        "sentence": {"type": "string"},
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "filler", "roles", "eid_set", "ntype"],
                "properties": {
                    "id":      {"type": "string"},
                    "filler":  {"type": "string"},
                    "roles":   {"type": "array", "items": {"type": "string"}},
                    "eid_set": {"type": "array", "items": {"type": "string"}},
                    "ntype":   {"enum": ["spo", "attr", "meta_out", "chv", "event"]}
                }
            }
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source", "target", "kind"],
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "kind":   {"enum": ["S-P", "P-O", "attr", "meta", "binder", "event-pred"]}
                }
            }
        },
        "layouts": {
            "type": "object",
            "properties": {
                "hulls": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["members"],
                        "properties": {
                            "eid": {"type": "string"},
                            "members": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            }
        }
    }
}

# Regex for stripping JS-style /* ... */ comments
_JSON_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)


def _strip_comments(text: str) -> str:
    """Remove all /* ... */ comments from JSON text."""
    return _JSON_COMMENT_RE.sub("", text)


def _patch_schema(data: Dict[str, Any]) -> None:
    """
    Dynamically extend the SCHEMA enums to accept any extra kinds or types
    found in the data (so the validator won't break on minor drifts).
    """
    # Allow new edge kinds
    edge_enum = SCHEMA["properties"]["edges"]["items"]["properties"]["kind"]["enum"]
    for edge in data.get("edges", []):
        kind = edge.get("kind")
        if kind and kind not in edge_enum:
            edge_enum.append(kind)
    # Allow new node types
    node_enum = SCHEMA["properties"]["nodes"]["items"]["properties"]["ntype"]["enum"]
    for node in data.get("nodes", []):
        ntype = node.get("ntype")
        if ntype and ntype not in node_enum:
            node_enum.append(ntype)


def validate_file(json_path: Path, strict: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate the JSON payload at `json_path` against the CHV graph schema.

    :param json_path: Path to the extracted-JSON payload file (.json)
    :param strict:    If True, stop at first schema violation (not used currently).
    :returns:         (ok, errors) where `ok` is True if no errors, and `errors` is a list of messages.
    """
    try:
        text = json_path.read_text(encoding="utf-8")
        text = _strip_comments(text)
        data = json.loads(text)
    except json.JSONDecodeError as e:
        # Invalid JSON syntax
        return False, [f"Invalid JSON ({e})"]

    # Extend enums for any new kinds/types in the data
    _patch_schema(data)

    # Collect all schema validation errors
    validator = Draft202012Validator(SCHEMA)
    errors: List[str] = [err.message for err in validator.iter_errors(data)]

    return (len(errors) == 0, errors)
