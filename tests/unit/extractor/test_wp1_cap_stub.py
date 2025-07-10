import pathlib
from hydraedge.extractor import wp1_cap_stub as wp1

# Sentences > 64 tokens to trigger truncation
LONG_SENT = (
    " ".join(f"w{i}" for i in range(80))
    + "."
)

def test_cap_len():
    res = wp1.run("docX", 0, LONG_SENT, cap_len=64)
    assert len(res["cap"].split()) == 64
    # original > 64 tokens ⇒ result shorter
    assert len(res["cap"].split()) < len(LONG_SENT.split())

def test_offsets_monotone():
    res = wp1.run("docX", 1, "Hello world.", cap_len=64)
    offs = res["offsets"]
    assert offs == sorted(offs), "Offsets must be increasing."

def test_stub_injection_needed():
    noverb = "Beautiful flowers in the garden."
    res = wp1.run("docX", 2, noverb)
    assert res["inject_stub"] is True

def test_stub_not_needed():
    ok = "The cat sat."
    res = wp1.run("docX", 3, ok)
    assert res["inject_stub"] is False
