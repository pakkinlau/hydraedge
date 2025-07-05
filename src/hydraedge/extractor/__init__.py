"""
hydraedge.extractor (lightweight façade)
=======================================

❱  *Keeps unit-tests & CI green* by **avoiding heavyweight imports** at
module-import time.  Nothing from HuggingFace / Torch / torchvision is
touched until you explicitly *ask* for SRL or CHV encoding.

The public surface remains::

    >>> from hydraedge.extractor import sentence_to_payload
"""

from importlib import import_module
from types     import ModuleType
from typing    import Any, Callable

from .api import extract  

__all__ = ["sentence_to_payload"]


# -- lazy proxy --------------------------------------------------------------
def _api() -> ModuleType:                        # never cached in globals()
    return import_module(".api",  package=__name__)


def __getattr__(name: str) -> Any:               # PEP-562 dynamic attribute
    if name in __all__:
        return getattr(_api(), name)
    raise AttributeError(name)
