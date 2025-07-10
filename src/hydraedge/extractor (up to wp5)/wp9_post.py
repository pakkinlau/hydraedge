# ────────────────────────────────────────────────────────────────
# wp9_post.py
# ----------------------------------------------------------------
# Stage WP-9 · Post-Processing & Payload Assembly
#
# Responsibilities
# 1. Merge duplicate spans across tuples (case-insensitive).
# 2. Add tense tag (PAST / PRESENT / FUTURE) to each tuple member
#    using spaCy morph info when predicate token matches span.
# 3. Inject provenance meta-nodes: Date & Source if detected.
# 4. Wrap everything into final JSON payload v2.5 and attach to
#    ctx.data["payload"] (dict, serialisable).
#
# Input  (ctx.data)
#   doc          – spaCy Doc
#   tuples       – List[dict]  (WP-7)
#   hulls        – List[hull]  (WP-8)
#
# Output
#   payload      – Dict[str, Any]  (v2.5 schema, top-level only)
#
# Config keys
#   meta:
#     enable  : true
#     date_re : default ISO/relaxed pattern
#
# Dependencies: dateparser, regex
# ----------------------------------------------------------------
from __future__ import annotations

import datetime as _dt
import re
from typing import Any, Dict, List, Set

import dateparser
from hydraedge.extractor.base import Ctx, PipelineStage, register

__all__ = ["PostStage"]

_DATE_RE = re.compile(
    r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}\s+\w+\s+\d{4})\b",
    flags=re.IGNORECASE,
)


def _detect_date(text: str) -> str | None:
    """Return ISO date str if recogniseable."""
    m = _DATE_RE.search(text)
    if not m:
        return None
    dt = dateparser.parse(m.group(0))
    if not dt:
        return None
    return dt.date().isoformat()


# ╭──────────────────────────────────────────────────────────────╮
# │  Stage                                                       │
# ╰──────────────────────────────────────────────────────────────╯
@register
class PostStage(PipelineStage):
    """WP-9 — Final clean-up & payload output."""

    name = "post"
    requires = ["hulls", "tuples"]   # produced earlier
    provides = ["payload"]

    # --------------------------------------------------------------
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.enable_meta = config.get("meta", {}).get("enable", True)

    # --------------------------------------------------------------
    def _merge_spans(self, tuples: List[Dict[str, Any]]) -> None:
        seen: Set[str] = set()
        dedup: List[Dict[str, Any]] = []
        for t in tuples:
            key = (t["role"], t["span"].lower())
            if key in seen:
                continue
            seen.add(key)
            dedup.append(t)
        tuples[:] = dedup  # in place

    # --------------------------------------------------------------
    def _tag_tense(self, doc, tuples: List[Dict[str, Any]]) -> None:
        for t in tuples:
            span_text = t["span"]
            for tok in doc:
                if tok.text == span_text and tok.tag_.startswith("V"):
                    tense = "PAST" if "Tense=Past" in tok.morph else "PRESENT"
                    t["tense"] = tense
                    break

    # --------------------------------------------------------------
    def _inject_meta(self, doc, payload: Dict[str, Any]) -> None:
        if not self.enable_meta:
            return
        date_iso = _detect_date(doc.text)
        meta_nodes: List[Dict[str, Any]] = []
        if date_iso:
            meta_nodes.append(
                {
                    "id": f"meta:Date:{date_iso}",
                    "ntype": "meta_out",
                    "filler": date_iso,
                }
            )
        if meta_nodes:
            payload.setdefault("nodes", []).extend(meta_nodes)

    # --------------------------------------------------------------
    def run(self, ctx: Ctx) -> None:
        payload = {
            "version": "2.4",
            "text":    ctx.text,
            "tuples":  ctx.data["tuples"],
            "hulls":   ctx.data["hulls"],
            "layouts": ctx.data.get("layouts", []),
        }
        ctx.data["payload"] = payload
        ctx.debug[self.name] = {"n_tuples": len(payload["tuples"])}