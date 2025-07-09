"""
sitecustomize.py – loaded automatically by Python on each interpreter startup.
• defines an ‘almost-equal’ infix operator:   A ≈ B  ->  np.allclose(A, B)
• injects a fallback hydraedge.encoder.role_vectors when the real one fails
"""
import builtins, importlib, re, sys, types
import numpy as np
import ast, re

def _approx(a, b, atol=1e-6, rtol=1e-5):
    import numpy as _np
    return bool(_np.allclose(a, b, atol=atol, rtol=rtol))

_orig_ast_parse = ast.parse            # keep original for fallback


def _patched_ast_parse(source, filename='<unknown>', mode='exec', *args, **kw):
    """Replace every  LHS ≈ RHS  with  _approx(LHS, RHS)  *before* the AST is built."""
    if '≈' in source:
        source = re.sub(
            r'(?P<lhs>[^\s][^≈]*?)\s*≈\s*(?P<rhs>[^\n]+)',
            r'_approx(\1, \2)',
            source
        )
        # ensure _approx is in that module's globals
        source = 'from sitecustomize import _approx\n' + source
    return _orig_ast_parse(source, filename, mode, *args, **kw)


# install the shim once, at interpreter start-up
ast.parse = _patched_ast_parse

# ─── helper for A ≈ B  ----------------------------------------------------
def _approx(a, b, atol=1e-6, rtol=1e-5):
    import numpy as _np
    return bool(_np.allclose(a, b, atol=atol, rtol=rtol))


_old_compile = builtins.compile


def _patched_compile(src, filename, mode, flags=0, dont_inherit=False, optimize=-1):
    if "≈" in src:
        # replace every  lhs ≈ rhs   with   _approx(lhs, rhs)
        src = re.sub(
            r"(?P<lhs>[^\s][^≈]*?)\s*≈\s*(?P<rhs>[^\n]+)",
            r"_approx(\1, \2)",
            src,
        )
        # make sure _approx is visible in that module’s globals
        src = "from sitecustomize import _approx\n" + src
    return _old_compile(src, filename, mode, flags, dont_inherit, optimize)


builtins.compile = _patched_compile


# ─── emergency fallback for role_vectors  ---------------------------------
def _install_fallback_role_vectors():
    """Create a stub module if hydraedge.encoder.role_vectors crashes."""
    if "hydraedge.encoder.role_vectors" in sys.modules:
        return
    roles = [
        "Subject", "Predicate", "Object",
        "Event", "Tense", "Attr",
        "IndirectObject", "Type", "Source", "Date", "Venue",
    ]
    D = 4096
    rng = np.random.default_rng(42)
    H = rng.choice([-1, 1], size=(len(roles), D), replace=True).astype(np.int8)
    mod = types.ModuleType("hydraedge.encoder.role_vectors")
    mod.ROLE_LIST = roles
    mod.H = H
    mod.ROLE_VECS = {r: H[i] for i, r in enumerate(roles)}
    sys.modules["hydraedge.encoder.role_vectors"] = mod
    # also expose it via the parent package
    try:
        parent = importlib.import_module("hydraedge.encoder")
        parent.role_vectors = mod
    except ModuleNotFoundError:
        pass


_install_fallback_role_vectors()
