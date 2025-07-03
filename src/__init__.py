"""
HydraEdge top-level namespace.

Exposes:
    • extract      – sentence-level event extractor (stub for now)
    • encode_chain – utility used in smoke tests
"""
from importlib import metadata as _md                             # optional
__version__ = "0.1.2"  # keep mypy happy

from .extractor import extract          # re-export
from .model.encode_utils import encode_chain   # re-export, see § 3

__all__ = ["extract", "encode_chain", "__version__"]
