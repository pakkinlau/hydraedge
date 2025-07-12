# ── src/hydraedge/schema/payload_schema.py ──────────────────────────────
"""Single-source-of-truth JSON-Schema loader (v 2.4).

* Robust against UTF-8 BOMs.
* Silently strips `/* comment */` blocks so we can keep
  human-readable notes in the schema file.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Path: …/schema/chv_v24.json   (same dir as this file)
_SCHEMA_PATH = Path(__file__).with_name("chv_v24.json")
_COMMENT_RE  = re.compile(r"/\*.*?\*/", re.S)          # C-style comments


def _load_schema(path: Path) -> dict:
    """Read + clean + parse the JSON schema."""
    raw = path.read_text(encoding="utf-8-sig")         # drops UTF-8 BOM if present
    raw = _COMMENT_RE.sub("", raw)                     # strip /* … */
    return json.loads(raw)


try:
    SCHEMA: dict = _load_schema(_SCHEMA_PATH)
except Exception as exc:                               # pragma: no cover
    raise RuntimeError(f"Could not load JSON schema at {_SCHEMA_PATH}: {exc}") from exc


__all__ = ["SCHEMA"]
