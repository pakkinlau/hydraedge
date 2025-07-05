"""
hydraedge.extractor.srl_hf
──────────────────────────
A 3-tier SRL loader

1. **AllenNLP** (decoded SRL archive) – _TODO_
2. **HF token-classification pipeline** – quick & light
3. **Heuristic spaCy fallback** – never breaks the CI
"""
from __future__ import annotations
import os, warnings
from typing import List, Dict

# ──────────────────────────────
# 1)  HF PIPELINE  (tier-2)
# ──────────────────────────────
_MODEL_ID = "liaad/srl-en_mbert-base"

def _build_hf_pipeline():
    from transformers import (                     # lazy-import – heavy!
        AutoTokenizer, AutoModelForTokenClassification, pipeline
    )
    try:
        tok  = AutoTokenizer.from_pretrained(_MODEL_ID)
        mdl  = AutoModelForTokenClassification.from_pretrained(_MODEL_ID)
    except OSError:
        raise RuntimeError("HF weights not yet in cache – pull them once, then re-run")
    return pipeline("token-classification",
                    model=mdl,
                    tokenizer=tok,
                    aggregation_strategy="simple")

# ──────────────────────────────
# 2)  SPA ~heuristic as last resort
# ──────────────────────────────
class _HeuristicSRL:           # **unchanged except for tagger-dup guard**
    def __init__(self):
        import spacy, en_core_web_sm                # 20 MB, cpu-only
        self.nlp = en_core_web_sm.load()
        if "tagger" not in self.nlp.pipe_names:     # ← fix E007 duplication
            self.nlp.add_pipe("tagger")
    def predict(self, sent: str) -> Dict:
        doc   = self.nlp(sent)
        tags  = ["O"] * len(doc)
        verbI = min((i for i,t in enumerate(doc) if t.pos_ == "VERB"), default=None)
        if verbI is not None:
            tags[verbI] = "B-V"
            if verbI > 0:           tags[verbI-1] = "B-ARG0"
            if verbI < len(doc)-1:  tags[verbI+1] = "B-ARG1"
        return {"words":[t.text for t in doc],
                "verbs":[{"tags":tags}]}

# ──────────────────────────────
# 3)  Singleton accessor
# ──────────────────────────────
_predictor_singleton = None

def get_predictor():
    """Return an object with .predict(sentence:str)->dict(verbs=[…])."""
    global _predictor_singleton
    if _predictor_singleton is not None:
        return _predictor_singleton
    try:
        _predictor_singleton = _build_hf_pipeline()
        print("✅  Using HF SRL pipeline")
        # wrap HF pipeline so that .predict looks like AllenNLP
        class _Wrapper:
            def __init__(self, pipe): self.pipe=pipe
            def predict(self,sent:str):
                raw = self.pipe(sent)        # list[dict]
                words = [r["word"] for r in raw]
                tags  = [r["entity"] for r in raw]
                return {"words":words, "verbs":[{"tags":tags}]}
        _predictor_singleton = _Wrapper(_predictor_singleton)
    except Exception as e:
        warnings.warn(f"⚠️  Falling back to heuristic SRL: {e}")
        _predictor_singleton = _HeuristicSRL()
    return _predictor_singleton


def run_srl(sentence: str) -> list[dict]:
    """
    Placeholder stub so that
        `from hydraedge.extractor.srl_hf import run_srl`
    always succeeds at import time.  Unit-tests will monkey-patch this
    to return their desired SRL frames.
    """
    return []  # real SRL lives elsewhere in your pipeline