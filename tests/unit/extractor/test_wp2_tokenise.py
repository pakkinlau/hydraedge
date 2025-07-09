# tests/unit/extractor/test_wp2_tokenise.py

def test_tokenise_roundtrip(cap_result, tokens):
    import re

    txt   = cap_result["text"]
    recon = " ".join(tok for tok, *_ in tokens)

    # First collapse spaces before punctuation (e.g., "billion ." → "billion.")
    # Then collapse spaces after dollar signs (e.g., "$ 1.65" → "$1.65")
    def norm(s: str) -> str:
        s = re.sub(r"\s+([.,])", r"\1", s)
        s = re.sub(r"\$\s+", "$", s)
        return s

    assert norm(recon) == txt

    # Ensure we still got (token, POS, idx) triples
    assert all(isinstance(t, tuple) and len(t) == 3 for t in tokens)
