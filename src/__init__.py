"""
Make `import src.serve.app` resolve to the real FastAPI app that lives in
`hydraedge.serve.app`.

Keep this file tiny: no project logic here – just import-path aliases.
"""
import importlib
import sys as _sys

# real serving package
_real_serve_pkg = importlib.import_module("hydraedge.serve")

# register alias modules so they import naturally
_sys.modules[__name__ + ".serve"] = _real_serve_pkg
_sys.modules[__name__ + ".serve.app"] = importlib.import_module(
    "hydraedge.serve.app"
)
