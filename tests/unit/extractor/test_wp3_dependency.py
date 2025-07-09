def test_dependency_len(tokens, deps):
    assert len(deps) == len(tokens)          # one arc per token
    # head indices are in-range
    n = len(tokens)
    assert all(0 <= h < n for _, h, _ in deps)
