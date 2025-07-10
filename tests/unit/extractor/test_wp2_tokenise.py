from hydraedge.extractor import wp1_cap_stub, wp2_tokenise


def _prep(sentence: str):
    cap = wp1_cap_stub.run("docT", 0, sentence, cap_len=64)
    return wp2_tokenise.run("docT", 0, cap["cap"])


def test_lengths_match():
    res = _prep("The quick brown fox jumps over the lazy dog.")
    n = len(res["tokens"])
    assert all(len(res[k]) == n for k in ("lemmas", "pos", "spans"))


def test_roundtrip():
    sent = "SpaCy splits punctuation correctly, e.g., 'hello!'"
    res = _prep(sent)
    recon = " ".join(res["tokens"])
    # Remove double-spaces generated around punct by join
    assert recon.replace(" ", "") == sent.replace(" ", "")


def test_cap_boundary():
    long = " ".join(f"t{i}" for i in range(100))
    cap = wp1_cap_stub.run("docT", 1, long, cap_len=64)
    res = wp2_tokenise.run("docT", 1, cap["cap"])
    assert len(res["tokens"]) <= 64
