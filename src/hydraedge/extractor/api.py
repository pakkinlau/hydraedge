"""
Public façade for Hydra-Edge extraction.

Every downstream import **must** continue to work::

    from hydraedge.extractor.api import extract
"""
from importlib import import_module
from typing import Any, Dict, Tuple, List

# lazy-import to avoid circulars / heavy deps at module load
_tuple_extractor = import_module("hydraedge.extractor.tuple_extractor")

# Re-export ------------------------------------------------------------------
def extract(sentence: str,
            meta: Dict[str, Any] | None = None,
            /,
            doc_id: str = "DOC1",
            sent_id: str = "0001",
            **kw) -> Tuple[Dict[str, Any], List[Tuple[str, str]]]:
    """
    Thin wrapper that forwards everything to
    :pyfunc:`hydraedge.extractor.tuple_extractor.extract`.
    """
    return _tuple_extractor.extract(sentence, meta or {}, doc_id, sent_id, **kw)
