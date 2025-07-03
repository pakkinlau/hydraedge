def test_encode_chain():
    from src.extractor import extract
    X = ["foo", "bar"]
    vecs = [extract(t) for t in X]
    assert len(vecs) == 2 and vecs[0].shape == vecs[1].shape