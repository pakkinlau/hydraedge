# src/hydraedge/extractor/wp7_rulemap.py

"""
WP-7: Learned or fallback rule-map for internal roles.

Tracks any “unseen” SRL tags so you can spot gaps.
"""
from __future__ import annotations
import os
import joblib
import numpy as np
from typing import Optional
from collections import Counter

# —— track any SRL labels we fall back on ——
_UNSEEN: Counter[str] = Counter()

# —— Helper featurizer (stub) —— 
def _featurize(srl_label: str, dep_label: str, verb: str, span: str) -> np.ndarray:
    # toy 4d features; replace with your real featurizer as needed
    return np.array([
        hash(srl_label) % 100 / 100.0,
        hash(dep_label ) % 100 / 100.0,
        len(verb)          / 10.0,
        len(span)          / 10.0,
    ], dtype=float)

class RoleClassifier:
    def __init__(self, model_path: str):
        self.clf = joblib.load(model_path)

    def predict(self,
                srl_label: str,
                dep_label: str,
                verb: str,
                span: str
               ) -> str:
        feats = _featurize(srl_label, dep_label, verb, span).reshape(1, -1)
        return self.clf.predict(feats)[0]

# —— Try to load the classifier if available —— 
_model_path = "models/role_classifier.joblib"
if os.path.isfile(_model_path):
    try:
        _ROLE_CLF: Optional[RoleClassifier] = RoleClassifier(_model_path)
    except Exception:
        _ROLE_CLF = None
else:
    _ROLE_CLF = None

def map_role(srl_label: str,
             dep_label: str,
             verb: str = "",
             span: str = ""
            ) -> str:
    """
    Map SRL tag + dep_label (optionally verb+span) to internal role.
    Uses learned classifier if available, else falls back to raw srl_label.
    Any fallback labels get counted in _UNSEEN.
    """
    # 1) try classifier
    if _ROLE_CLF is not None:
        try:
            return _ROLE_CLF.predict(srl_label, dep_label, verb, span)
        except Exception:
            pass

    # 2) fallback to propbank tag
    _UNSEEN[srl_label] += 1
    return srl_label

def get_unseen_counts() -> Counter[str]:
    """After running your pipeline, call this to see which tags fell back."""
    return _UNSEEN
