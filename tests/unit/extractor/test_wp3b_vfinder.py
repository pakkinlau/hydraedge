# -*- coding: utf-8 -*-
"""
Unit tests for the VerbFinder helper (no spaCy factory needed).
"""
import spacy
import pytest
from hydraedge.extractor.wp3b_vfinder import VerbFinder

nlp = spacy.blank("en")  # lightweight pipeline


@pytest.mark.parametrize(
    "sent,expected",
    [
        ("The cat sits on the mat.", True),
        ("No verb here", False),
        ("To be or not to be", True),
    ],
)
def test_has_verb(sent, expected):
    doc = nlp(sent)
    assert VerbFinder.has_verb(doc) is expected
