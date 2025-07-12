from pathlib import Path
import re
import json

import pytest

from hydraedge.schema.validator import validate_payload

# ---------- helpers ---------------------------------------------------------
_SAMPLE = Path("data/sample-record-data-graph/example_payload_schema_2.4.json")


def _load_json_as_str(path: Path) -> str:
    """Read file, strip /* … */ comments, return raw JSON string."""
    txt = path.read_text(encoding="utf-8")
    return re.sub(r"/\*.*?\*/", "", txt, flags=re.S)


# ---------------------------------------------------------------------------

OK_JSON = _load_json_as_str(_SAMPLE)


def test_validator_json_ok():
    ok, errors = validate_payload(OK_JSON)
    assert ok, f"validator unexpectedly failed: {errors}"
