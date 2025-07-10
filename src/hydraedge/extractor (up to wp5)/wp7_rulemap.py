# ────────────────────────────────────────────────────────────────
# wp7_rulemap.py
# ----------------------------------------------------------------
# Stage WP-7 · Rule-map → Raw Tuple Conversion
#
# Consumes SRL frames produced by WP-4 and emits a *raw* list of
# tuples, ready for hull grouping (WP-8) and post-processing (WP-9).
#
# Tuple schema (intermediate)
#   {
#     "eid" : str,            # event id (one per predicate)
#     "role": str,            # ARG0 / ARG1 / TMP / ...
#     "span": str,            # surface text
#   }
#
# Input  (ctx.data)
#   doc          : spaCy Doc      (WP-2)
#   frames       : List[dict]     (WP-4)
#   alias_map    : {surface: alias_key} (WP-5)
#   may_need_stub: bool           (WP-1)
#
# Output (ctx.data)
#   tuples       : List[dict]  (raw tuples, no hulls)
#   debug["rulemap"] : diagnostics
#
# Configuration – none
# ----------------------------------------------------------------
from __future__ import annotations

import itertools
import logging
import uuid
from typing import Any, Dict, List

from hydraedge.extractor.base import Ctx, PipelineStage, register

logger = logging.getLogger(__name__)

__all__ = ["RuleMapStage"]


@register
class RuleMapStage(PipelineStage):
    """WP-7 — Convert SRL frames into raw (role, span) tuples."""

    name = "rulemap"
    requires = ["doc", "frames", "alias_map", "may_need_stub"]
    provides = ["tuples"]

    # --------------------------------------------------------------
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)

    # --------------------------------------------------------------
    def run(self, ctx: Ctx) -> None:  # noqa: D401
        doc = ctx.data["doc"]
        frames: List[Dict[str, Any]] = ctx.data["frames"]
        alias_map: Dict[str, str] = ctx.data["alias_map"]
        tuples: List[Dict[str, str]] = []

        # group frames by predicate lemma → eid
        eid_of_pred: Dict[str, str] = {}

        def _get_eid(pred: str) -> str:
            if pred not in eid_of_pred:
                eid_of_pred[pred] = str(uuid.uuid4())[:8]
            return eid_of_pred[pred]

        for fr in frames:
            pred = fr["predicate"]
            role = fr["role"]
            span = fr["span"].strip()
            eid = _get_eid(pred)

            tuples.append({"eid": eid, "role": role, "span": span})

        # Optional SentenceStub when SRL failed
        if ctx.data["may_need_stub"] and not tuples:
            eid = str(uuid.uuid4())[:8]
            tuples.append({"eid": eid, "role": "SentenceStub", "span": "[stub]"})

        # Attach alias_key if available (used later by encoder)
        for tup in tuples:
            surface = tup["span"].lower()
            alias = alias_map.get(surface)
            if alias:
                tup["alias_key"] = alias

        ctx.data["tuples"] = tuples
        ctx.debug[self.name] = {
            "n_predicates": len(eid_of_pred),
            "n_tuples": len(tuples),
            "stub_injected": ctx.data["may_need_stub"] and not frames,
        }
