#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from hydraedge.extractor import wp3b_vfinder as vf

@pytest.mark.parametrize(
    ("sent", "expect"),
    [
        ("The cat sits on the mat.", True),
        ("No verb here", False),
        ("To be or not to be", True),
    ],
)
def test_has_verb(sent: str, expect: bool) -> None:
    assert vf.has_verb(sent) is expect

def test_run_structure() -> None:
    info = vf.run("docX", 7, "Nothing to do")
    assert set(info.keys()) == {"doc_id", "sent_id", "skip_srl"}
    assert info["doc_id"] == "docX"
    assert info["sent_id"] == 7
    # "Nothing to do" has verb "do", so skip_srl=False
    assert info["skip_srl"] is False
