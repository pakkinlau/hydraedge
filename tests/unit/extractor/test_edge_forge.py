from hydraedge.extractor.edge_rules import build_edges
from hydraedge.extractor.protocols import Node

def test_basic_spo_chain():
    nodes = [
        Node(id="spo:see@e1", filler="see", alias_key="see",
             roles=["Predicate"], eid_set=["e1"], ntype="spo", char_start=2, char_end=5),
        Node(id="spo:I@e1",   filler="I", alias_key="i",
             roles=["Subject"], eid_set=["e1"], ntype="spo", char_start=0, char_end=1),
        Node(id="spo:dog@e1", filler="dog", alias_key="dog",
             roles=["Object"],  eid_set=["e1"], ntype="spo", char_start=14, char_end=17),
    ]
    edges = build_edges(nodes, "I see dog")
    kinds = {(e.source, e.target, e.kind) for e in edges}
    assert ("spo:I@e1","spo:see@e1","S-P") in kinds
    assert ("spo:see@e1","spo:dog@e1","P-O") in kinds
