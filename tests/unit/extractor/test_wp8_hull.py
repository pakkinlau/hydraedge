def test_hull_structure(hulls, tuples_result):
    # expect at least one hull or zero if no tuples
    if tuples_result:
        assert hulls, "expected hulls for non-empty tuple set"
        root = hulls[0]
        assert {"eid", "members", "children"} <= root.keys()
