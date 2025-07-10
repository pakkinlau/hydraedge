# ────────────────────────────────────────────────────────────────────────────────
# HydraEdge · encoder package initialiser (lazy-load variant)
# Save as: src/hydraedge/encoder/__init__.py
# -------------------------------------------------------------------------------
"""
HydraEdge encoder namespace.

We deliberately **avoid eager imports** to prevent circular-initialisation
problems (e.g. chv_math → encoder → chv_math).  Sub-modules are exposed
lazily via ``__getattr__`` the first time they are accessed.

Public API
----------
encoder.chv_math
encoder.chv_encoder
encoder.ep0_pre_check
# + any future encoder.* modules listed in ``_LAZY_EXPORTS``

Example
-------
>>> from hydraedge.encoder import chv_math
>>> chv_math.dot_sign(...)
"""

from importlib import import_module
import sys
from types import ModuleType
from typing import Final

__all__ = [
    "chv_math",
    "chv_encoder",
    "ep0_pre_check",
]

_LAZY_EXPORTS: Final[set[str]] = set(__all__)


def __getattr__(name: str) -> ModuleType:  # noqa: D401, N802
    """Dynamically import *encoder.name* on first access."""
    if name in _LAZY_EXPORTS:
        full_name = f"{__name__}.{name}"
        mod = import_module(full_name)
        sys.modules[full_name] = mod
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:  # noqa: D401
    """Allow static analysers / `dir()` to discover lazy exports."""
    return sorted(list(globals().keys()) + list(_LAZY_EXPORTS))
