def test_srl_shapes(tokens, srl_frames):
    assert srl_frames, "SRL found no frames"
    for frame in srl_frames:
        assert len(frame["words"]) == len(tokens)
        assert len(frame["tags"])  == len(tokens)
        vi = frame["verb_index"]
        assert frame["tags"][vi] == "B-V"
