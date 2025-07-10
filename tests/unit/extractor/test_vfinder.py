import spacy
from hydraedge.extractor.wp3b_vfinder import VerbFinder

nlp = spacy.load("en_core_web_sm", disable=["ner"])
nlp.add_pipe("verb_finder", after="parser")


def test_has_verb_positive() -> None:
    doc = nlp("The cat sat on the mat.")
    assert VerbFinder.has_verb(doc) is True


def test_has_verb_negative() -> None:
    doc = nlp("Hello world!")
    assert VerbFinder.has_verb(doc) is False
