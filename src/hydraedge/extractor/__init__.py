"""
hydraedge.extractor
~~~~~~~~~~~~~~~~~~~
Deterministic tuple-extraction pipeline (§ 1.2).

Usage
-----
>>> from hydraedge.extractor import extract_sentence
>>> payload = extract_sentence("In 2006 Google acquired YouTube for $1.65 billion.")
>>> print(payload["version"])      # '2.4'
"""
from .cli import extract_sentence, extract_doc
__all__ = ["extract_sentence", "extract_doc"]
