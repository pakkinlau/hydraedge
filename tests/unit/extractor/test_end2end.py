import json, pytest
from hydraedge.extractor.cli import extract_sentence
from hydraedge.extractor.wp1_cap_stub import MAX_LEN

def test_full_payload_structure(payload):
    assert payload["version"] == "2.4"
    assert "tuples"   in payload and payload["tuples"]
    assert "layouts"  in payload
    # no tuple span exceeds max cap length
    for t in payload["tuples"]:
        assert t["span"] and len(t["span"].split()) <= MAX_LEN

def test_determinism(sample_sentence):
    p1 = extract_sentence(sample_sentence)
    p2 = extract_sentence(sample_sentence)
    h  = pytest._hydra_hash
    assert h(p1) == h(p2), "extractor is non-deterministic!"
