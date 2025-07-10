from hydraedge.extractor import (
    wp1_cap_stub, wp2_tokenise, wp3_dependency, wp4_srl, wp5_alias
)

def _aliases(sentence: str):
    cap = wp1_cap_stub.run("doc", 0, sentence)
    tok = wp2_tokenise.run("doc", 0, cap["cap"])
    dep = wp3_dependency.run("doc", 0, cap["cap"])
    srl = wp4_srl.run("doc", 0, cap["cap"])
    return tok, wp5_alias.run("doc", 0, tok, srl)

def test_length_matches_tokens():
    tok, ali = _aliases("Cats and felines are synonyms.")
    assert len(ali["alias_keys"]) == len(tok["tokens"])

def test_gazetteer_hit():
    _, ali = _aliases("USA and America cooperate.")
    assert any(k in {"united_states", "united states"} for k in ali["alias_keys"])

def test_lemma_fallback():
    _, ali = _aliases("Foobarword nonexistent.")
    assert ali["alias_keys"][-2] == "nonexistent"
