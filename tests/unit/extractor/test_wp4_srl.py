from hydraedge.extractor import wp1_cap_stub, wp4_srl


def _run(s):
    cap = wp1_cap_stub.run("d", 0, s)
    return wp4_srl.run("d", 0, cap["cap"])


def test_pred_double():
    res = _run("John eats and sleeps.")
    assert len(res["predicates"]) >= 2

def test_roles_present():
    res = _run("Mary gave John a gift.")
    roles = res["roles"][0]
    assert "ARG0" in roles and "ARG1" in roles

def test_no_verb_empty():
    res = _run("Beautiful flowers in the garden.")
    assert res["predicates"] == [] and res["roles"] == []
