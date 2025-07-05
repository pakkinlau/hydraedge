"""
hydraedge.extractor.tuple_extractor
-----------------------------------
Minimal yet deterministic extractor that:

• Runs SRL if available (liaad/srl-en_xlmr-large) otherwise falls back to
  a tiny regex heuristic so the module always imports.
• Injects a *SentenceStub* node when SRL returns **no** frames (unit-test
  expectation).
• Returns JSON-serialisable v2.4 payload **and** a binarised CHV vector.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Tuple

import numpy as np
from pydantic import BaseModel, Field

# ── project-local helpers ─────────────────────────────────────────────
from ..encoder.chv_encoder import encode_chv, filler_vec_from_token
from ..encoder.role_vectors import ROLE_VECTORS, ROLES
from .alias import resolve_alias

# ──────────────────────────────────────────────────────────────────────
# Pydantic DTOs (kept tiny – just what tests access)
# ──────────────────────────────────────────────────────────────────────
class Node(BaseModel):
    id: str
    filler: str
    alias_key: str
    roles: List[str]
    ntype: str = "spo"
    eid_set: List[str] = Field(default_factory=list)
    char_start: int = 0
    char_end: int = 0


class Edge(BaseModel):
    source: str
    target: str
    kind: str


class Payload(BaseModel):
    version: str
    sentence: str
    nodes: List[Node]
    edges: List[Edge]
    layouts: dict
    chv: List[int]  # <-- JSON-friendly (was ndarray)


# ──────────────────────────────────────────────────────────────────────
# Optional SRL backend – falls back gracefully
# ──────────────────────────────────────────────────────────────────────
try:
    from srl import SRL_Predictor  # type: ignore
    from transformers import AutoModelForTokenClassification, AutoTokenizer  # noqa: E402

    _tok = AutoTokenizer.from_pretrained("liaad/srl-en_xlmr-large")
    _mdl = AutoModelForTokenClassification.from_pretrained("liaad/srl-en_xlmr-large")
    _SRL = SRL_Predictor(model=_mdl, tokenizer=_tok, batch=1)

    def _frames(sentence: str) -> List[dict[str, Any]]:
        """Real PropBank frames."""
        return _SRL.predict(sentence)["verbs"]

except ModuleNotFoundError:  # pragma: no cover – still testable
    _VERB = re.compile(r"\b\w+(ed|ing|s)\b", re.I)

    def _frames(sentence: str) -> List[dict[str, Any]]:  # noqa: D401
        """Ultra-simple SPO splitter so imports never fail."""
        words = sentence.rstrip(".").split()
        if len(words) < 3:
            return []
        pred_idx, pred = next(
            ((i, w) for i, w in enumerate(words) if _VERB.match(w)), (1, words[1])
        )
        tags = ["B-ARG0" if i == 0 else "B-ARG1" if i == len(words) - 1 else "O" for i in range(len(words))]
        return [{"verb": pred, "words": words, "tags": tags}]


# ──────────────────────────────────────────────────────────────────────
# Tiny tag→role map (good enough for unit-tests)
# ──────────────────────────────────────────────────────────────────────
def _propbank_to_role(tag: str) -> str | None:
    if tag == "B-ARG0":
        return "Subject"
    if tag in ("B-ARG1", "B-ARG2"):
        return "Object"
    if tag.startswith("B-ARGM-LOC"):
        return "IndirectObject"
    if tag.startswith("B-ARGM-MNR"):
        return "Attr"
    return None


# ──────────────────────────────────────────────────────────────────────
# Main helper – this is what the tests invoke
# ──────────────────────────────────────────────────────────────────────
def to_json(sentence: str, meta: Dict[str, str] | None = None) -> Payload:
    meta = meta or {}
    frames = _frames(sentence)

    nodes: list[Node] = []
    edges: list[Edge] = []
    tuples: list[tuple[str, np.ndarray]] = []
    eid_counter = 1

    if not frames:
        # — SentenceStub injection (unit-test checks this) —
        stub_id = f"stub:{hashlib.md5(sentence.encode()).hexdigest()[:6]}"
        nodes.append(
            Node(
                id=stub_id,
                filler=sentence,
                alias_key=sentence.lower(),
                roles=["Sentence"],
                ntype="SentenceStub",
            )
        )
    else:
        # — normal SRL walk —
        for fr in frames:
            eid = f"e{eid_counter}"
            pred = fr["verb"]
            pred_id = f"spo:{pred}@{eid}"

            nodes.append(
                Node(
                    id=pred_id,
                    filler=pred,
                    alias_key=resolve_alias(pred),
                    roles=["Predicate"],
                    eid_set=[eid],
                    char_start=sentence.find(pred),
                    char_end=sentence.find(pred) + len(pred),
                )
            )

            for w, tag in zip(fr["words"], fr["tags"]):
                role = _propbank_to_role(tag)
                if role is None:
                    continue
                nid = f"spo:{w}@{eid}"
                if nid not in {n.id for n in nodes}:
                    nodes.append(
                        Node(
                            id=nid,
                            filler=w,
                            alias_key=resolve_alias(w),
                            roles=[role],
                            eid_set=[eid],
                            char_start=sentence.find(w),
                            char_end=sentence.find(w) + len(w),
                        )
                    )

                kind = {"Subject": "S-P", "Object": "P-O"}.get(role, "attr")
                edges.append(
                    Edge(
                        source=pred_id if kind == "P-O" else nid,
                        target=nid if kind == "P-O" else pred_id,
                        kind=kind,
                    )
                )

                tuples.append((role, filler_vec_from_token(w)))

            eid_counter += 1

    # — CHV encode & make JSON-safe —
    chv = encode_chv(tuples) if tuples else np.ones(4096, dtype=np.int8)
    chv_list = chv.astype(int).tolist()

    return Payload(
        version="2.4",
        sentence=sentence,
        nodes=nodes,
        edges=edges,
        layouts={"hulls": []},
        chv=chv_list,
    )
