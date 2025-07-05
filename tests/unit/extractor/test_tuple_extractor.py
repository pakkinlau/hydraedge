import json, numpy as np, pytest
from hydraedge.extractor.tuple_extractor import to_json

def test_stub_injection():
    js = to_json("Wow!", {})      # SRL will return []
    stubs = [n for n in js.nodes if n.ntype=="SentenceStub"]
    assert len(stubs)==1 and stubs[0].filler.lower()=="wow"

def test_alias_unique():
    js = to_json("US researchers, U.S. scientists", {})
    keys = [n.alias_key for n in js.nodes]
    assert len(keys) == len(set(keys))

def test_schema_v24(tmp_path):
    from scripts.validate_json import check_file
    out = tmp_path/"one.jsonl"; out.write_text(json.dumps(to_json("He left.",{}).model_dump()))
    assert check_file(out, schema="2.4")==0
