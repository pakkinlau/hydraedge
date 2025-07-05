"""
Pass-0: Tokenization & Tagging
--------------------------------
Loads spaCy, runs the transformer pipeline to produce:
  - tokens with text, lemma, POS tag, dep label
  - accurate char_start & char_end
  - head index for dependency tree

This module exports:
  - load_tokenizer()
  - tokenize_and_tag(sentence: str) -> list[dict]

Each dict:
  {
    "text": str,
    "lemma": str,
    "pos": str,
    "dep": str,
    "head": int,
    "char_start": int,
    "char_end": int
  }

"""
import spacy
from spacy.tokens import Doc

_tokenizer = None

def load_tokenizer(model: str = "en_core_web_trf", disable: list[str] = ["ner"]):
    """
    Initialize and cache the spaCy pipeline.
    Args:
      model: Name of the spaCy model.
      disable: list of pipeline components to disable for speed.
    Returns:
      The loaded spaCy NLP pipeline.
    """
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = spacy.load(model, exclude=disable)
        # ensure we have sufficient max_length
        _tokenizer.max_length = max(_tokenizer.max_length, 10_000)
    return _tokenizer


def tokenize_and_tag(sentence: str):
    """
    Tokenize and annotate a sentence.
    Args:
      sentence: the input text string.
    Returns:
      A list of token dicts with text, lemma, POS, dependency, head index, and char offsets.
    """
    nlp = load_tokenizer()
    doc: Doc = nlp(sentence)
    tokens = []
    for token in doc:
        tokens.append({
            "text": token.text,
            "lemma": token.lemma_,
            "pos": token.pos_,
            "dep": token.dep_,
            "head": token.head.i,
            "char_start": token.idx,
            "char_end": token.idx + len(token.text)
        })
    return tokens


if __name__ == "__main__":
    # Quick smoke test
    sample = "I saw a white dog chase the brown cat quickly in the backyard."
    for t in tokenize_and_tag(sample):
        print(f"{t['text']:<12} lemma={t['lemma']:<10} pos={t['pos']:<5} dep={t['dep']:<8} head={t['head']:<2} span=({t['char_start']},{t['char_end']})")
