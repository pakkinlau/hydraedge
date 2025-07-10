# ==============================================================================
# 2. tests/unit/encoder/test_ep0_pre_check.py
# ==============================================================================
"""Pytest for Stage E0.

Run with:  pytest tests/unit/encoder/test_ep0_pre_check.py -q
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Generator

import pytest

from hydraedge.encoder.ep0_pre_check import PayloadValidationError, validate

# ------------------------------------------------------------------------------
# Helpers – load sample payload --------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[3]  # …/workspace
_SAMPLE_JSON = _REPO_ROOT / "data" / "sample" / "sample_extracted_JSON.json"
_ROLE_TSV = _REPO_ROOT / "data" / "sample" / "roles.tsv"


def _load_payload() -> dict:
    with _SAMPLE_JSON.open(encoding="utf‑8") as fh:
        return json.load(fh)


def _load_roles() -> set[str]:
    return {
        line.split("\t", 1)[0]
        for line in _ROLE_TSV.read_text("utf‑8").splitlines()
        if line.strip()
    }

# ------------------------------------------------------------------------------
# Test cases --------------------------------------------------------------------


def test_valid_sample_passes() -> None:
    payload = _load_payload()
    validate(payload, _load_roles())  # should raise nothing


def test_duplicate_alias_key_fails() -> None:
    payload = _load_payload()
    # duplicate alias_key of first spo node
    dup_key = payload["nodes"][0]["alias_key"]
    payload["nodes"].append(
        {
            "id": "dup1",
            "ntype": "spo",
            "filler": "duplicate",
            "roles": ["SUBJ"],
            "eid_set": ["e99"],
            "span": [0, 9],
            "alias_key": dup_key,  # ← duplicate
        }
    )
    with pytest.raises(PayloadValidationError):
        validate(payload, _load_roles())
