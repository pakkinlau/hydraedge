from hydraedge.extractor import wp1_cap_stub, wp2_tokenise, wp3_dependency


def _prep(sentence: str):
    cap = wp1_cap_stub.run("docD", 0, sentence, cap_len=64)
    tok = wp2_tokenise.run("docD", 0, cap["cap"])
    return tok, wp3_dependency.run("docD", 0, cap["cap"])


def test_lengths_match():
    tok, dep = _prep("The cat sat on the mat.")
    n = len(tok["tokens"])
    assert len(dep["heads"]) == n == len(dep["deps"])


def test_root_marked_minus_one():
    _, dep = _prep("The quick brown fox jumps.")
    assert dep["root"] != -1
    assert dep["heads"][dep["root"]] == -1


def test_head_indices_in_range():
    tok, dep = _prep("A very small sentence.")
    n = len(tok["tokens"])
    assert all((h == -1) or (0 <= h < n) for h in dep["heads"])
