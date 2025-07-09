def test_cap_stub_length(cap_result, sample_sentence):
    txt = cap_result["text"]
    assert isinstance(txt, str)
    assert len(txt.split()) <= 65            # ≤ 64 + “…”
    if len(sample_sentence.split()) > 64:
        assert txt.endswith("…")
