###########################
# File: tests/unit/encoder/test_ep0b_data_typle_check.py
###########################
"""Unit tests for *ep0b_data_typle_check*.

Run with::

    pytest -q
"""
from pathlib import Path
import pytest

from hydraedge.encoder.ep0b_data_typle_check import validate_file


# ---------------------------------------------------------------------------
# Sample fixtures (parametrised over the two user‑supplied JSONs)
# ---------------------------------------------------------------------------
SAMPLES = [
    Path("data/sample/sample_extracted_JSON.json"),
    Path("data/sample/example_payload_batch5c.json"),
]


@pytest.mark.parametrize("json_path", SAMPLES, ids=lambda p: p.name)
def test_payload_shape(json_path: Path):
    """Fails if *any* structural rule in the validator is violated.

    *We purposefully do NOT attempt to predict whether a given file should
    pass or fail*; the project’s CI will surface problems by turning this
    test red when the extractor emits malformed payloads.
    """
    ok, errors = validate_file(json_path, strict=False)

    if not ok:
        pretty = "\n  • " + "\n  • ".join(errors)
        pytest.fail(f"{json_path} failed schema check:{pretty}")


if __name__ == "__main__":
    # Allow ad‑hoc runs via `python test_ep0b_data_typle_check.py`
    import sys, pytest as _pytest

    sys.exit(_pytest.main([__file__]))
