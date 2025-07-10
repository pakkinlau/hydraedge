# -*- coding: utf-8 -*-
"""
End-to-end behavioural tests for the extractor pipeline.
"""

def test_determinism(extract_sentence_debug):
    s = "The cat sat on the mat."
    first  = extract_sentence_debug(s)
    second = extract_sentence_debug(s)
    assert first == second, "Pipeline must be deterministic."

def test_full_payload_structure(payload):
    # Version tag and mandatory sections
    assert payload["version"] == "2.4"
    assert payload["tuples"],  "tuples must be non-empty"
    assert payload["hulls"],   "hulls must be non-empty"
    # layouts key is always present (may be empty list)
    assert "layouts" in payload

def test_srl_skipped_when_no_verb(extract_sentence_debug):
    dbg = extract_sentence_debug("No verbs here.")
    assert dbg["meta"]["skip_srl"] is True
