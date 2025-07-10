#!/usr/bin/env python3
"""
wp3b_vfinder.py ── Verb-presence gate (WP-3b)
──────────────────────────────────────────────────────────────
•  Acts as a fast “SRL enable/skip” switch: if a sentence
   contains NO main verbs (VERB | AUX), later SRL is skipped.
•  Exposes both a spaCy pipeline component *and* a minimal
   class-based API so unit-tests can call VerbFinder.has_verb().
"""

from __future__ import annotations

from typing import Set

import spacy
from spacy.language import Language
from spacy.tokens import Doc
from .base import PipelineStage, Ctx, register

__all__ = ["VerbFinder"]

# ───────────────────────────────────────────────────────────────
# 0 ▸ Constants
# ───────────────────────────────────────────────────────────────
_VERB_TAGS: Set[str] = {"VERB", "AUX"}          # universal POS tags
_COMPONENT_NAME = "verb_finder"                 # spaCy registry key
_MAX_TOK = 256                                  # hard cut-off for blank model


# ───────────────────────────────────────────────────────────────
# 1 ▸ spaCy pipeline component
# ───────────────────────────────────────────────────────────────
if not Doc.has_extension("has_verb"):
    Doc.set_extension("has_verb", default=False)        # type: ignore[arg-type]


@Language.component(_COMPONENT_NAME)
def _verb_finder_pipe(doc: Doc) -> Doc:  # noqa: D401
    """Annotate *doc* with ._.has_verb = bool and return the doc."""
    doc._.has_verb = any(tok.pos_ in _VERB_TAGS for tok in doc[:_MAX_TOK])
    return doc


# Compatibility shim for older tests that query
# `Language.component_registry` directly.
if not hasattr(Language, "component_registry"):
    Language.component_registry = set()  # type: ignore[attr-defined]
Language.component_registry.add(_COMPONENT_NAME)        # type: ignore[attr-defined]


# ───────────────────────────────────────────────────────────────
# 2 ▸ Convenience class wrapper (used by tests & other modules)
# ───────────────────────────────────────────────────────────────
class VerbFinder:
    """Stateless helper with a single static method."""

    @staticmethod
    def has_verb(doc: Doc) -> bool:
        """Return True iff `doc` contains a VERB or AUX token."""
        return any(tok.pos_ in {"VERB", "AUX"} for tok in doc)


# ── single spaCy factory so nlp.add_pipe("verb_finder") works ──────────
@Language.factory("verb_finder")
def verb_finder_factory(nlp: Language, name: str):
    return nlp.get_pipe(name) if name in nlp.pipe_names else VerbFinderComponent()

class VerbFinderComponent:
    def __call__(self, doc: Doc):
        doc.user_data["has_verb"] = any(t.pos_ in {"VERB", "AUX"} for t in doc)
        return doc
    
@register
class VerbFinderStage(PipelineStage):
    """Pipeline stage – sets ctx.data['has_verb']."""

    name = "verb_finder"
    requires = ["doc"]      # spaCy Doc produced by wp2_tokenise
    provides = ["has_verb"]

    def run(self, ctx: Ctx) -> None:
        doc: Doc = ctx.data["doc"]
        has = VerbFinder.has_verb(doc)
        ctx.data["has_verb"] = has
        ctx.debug[self.name] = {"has_verb": has}