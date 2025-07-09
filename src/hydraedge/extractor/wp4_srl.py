"""
wp4_srl.py  –  SRL verb-frame extractor (AllenNLP-free, marker-based)
───────────────────────────────────────────────────────────────────────────
• Uses the "dannashao/bert-base-uncased-finetuned-srl_arg" checkpoint via HF’s
  token-classification pipeline with aggregation_strategy="simple".
• Emits one frame per detected verb, aligning ARG spans via spaCy subtrees.
• Produces AllenNLP-compatible frames so downstream CLI needs no edits.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any
import torch
import spacy
from transformers import pipeline, AutoTokenizer

# ── configuration ─────────────────────────────────────────────────
MODEL_NAME = "dannashao/bert-base-uncased-finetuned-srl_arg"
DEVICE_ID  = 0 if torch.cuda.is_available() else -1
_VERB_RE   = re.compile(r"^[Vv][BDGNPZ]")  # Penn VB* tags

# ── load heavy resources once only ─────────────────────────────────
_nlp = spacy.load("en_core_web_sm", disable=["ner"])
_tok = AutoTokenizer.from_pretrained(MODEL_NAME)
_srl = pipeline(
    task="token-classification",
    model=MODEL_NAME,
    tokenizer=_tok,
    aggregation_strategy="simple",
    device=DEVICE_ID,
)


def _verb_indices(doc: spacy.tokens.Doc) -> List[int]:
    """Return indices of tokens with VB* POS tags."""
    return [i for i, tok in enumerate(doc) if _VERB_RE.match(tok.tag_)]


def _span_token_ids(span_start: int, span_end: int,
                    doc: spacy.tokens.Doc) -> List[int]:
    """
    Tokens covered by char offsets [span_start, span_end).
    Useful when SRL spans don't align perfectly.
    """
    ids: List[int] = []
    for tok in doc:
        if tok.idx >= span_end:
            break
        if tok.idx + len(tok) <= span_start:
            continue
        ids.append(tok.i)
    return ids


def srl_spans(sentence: str) -> List[Dict[str, Any]]:
    """
    Extract SRL frames in AllenNLP format:
    [
      {
        "verb": str,
        "verb_index": int,
        "words": List[str],
        "tags": List[str],     # BIO, e.g. B-ARG0, I-ARG1, B-V
        "description": str
      },
      ...
    ]
    """
    doc    = _nlp(sentence)
    tokens = [tok.text for tok in doc]
    frames: List[Dict[str, Any]] = []

    for frame_no, v_idx in enumerate(_verb_indices(doc)):
        # 1) Mark the verb for the SRL model
        marked = tokens.copy()
        marked[v_idx] = "[V] " + tokens[v_idx]
        text_marked = " ".join(marked)

        # 2) Run SRL
        spans = _srl(text_marked)

        # 3) Initialize BIO tags
        tags = ["O"] * len(tokens)
        tags[v_idx] = "B-V"

        # 4) Fill in argument spans
        for sp in spans:
            role = sp.get("entity_group") or sp.get("entity")
            if role in {"_", "B-V"}:
                continue
            # Remove SRL marker if present
            span_txt = sp.get("word", "").replace("[V] ", "")
            start, end = sp.get("start", 0), sp.get("end", 0)
            t_ids = _span_token_ids(start, end, doc)
            if not t_ids:
                continue
            tags[t_ids[0]] = f"B-{role}"
            for tid in t_ids[1:]:
                tags[tid] = f"I-{role}"

        frames.append({
            "verb"       : doc[v_idx].text,
            "verb_index" : v_idx,
            "words"      : tokens,
            "tags"       : tags,
            "description": f"e{frame_no}[{doc[v_idx].lemma_}]",
        })

    return frames
