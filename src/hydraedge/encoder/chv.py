"""
Compatibility shim – re-exports the real implementation that lives in
`chv_encoder.py`, so that both

    from hydraedge.encoder import chv_encoder
and
    from hydraedge.encoder import chv

work identically.
"""
from .chv_encoder import *        # noqa: F401,F403
