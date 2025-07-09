#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli.py  ·  HydraEdge extractor command-line interface
-----------------------------------------------------
Orchestrates the extraction work-packs for sentences or documents,
with a dual-pass SRL pre-check via wp3b_vfinder.
"""

from __future__ import annotations
from typing import Dict, Any, List

# 1) Token-cap & stub
from .wp1_cap_stub    import cap_and_stub as cap_stub
# 2) Tokenisation + POS
from .wp2_tokenise    import tokenise
# 3) Dependency parse
from .wp3_dependency  import run as parse_deps
# 3b) Fast verb-finder gate
from .wp3b_vfinder    import run as verb_finder
# 4) SRL frames
from .wp4_srl         import run as run_srl
# 5) Alias resolution
from .wp5_alias       import run as resolve_alias
# 6) Role lookup
from .wp6_roles       import run as lookup_roles
# 7) Rule-map → raw tuples
from .wp7_rulemap     import run as apply_rules
# 8) Nested-hull recursion
from .wp8_hull        import run as build_hulls
# 9) Post-processing (merge spans, tense, etc.)
from .wp9_post        import run as post_process

def extract_sentence(
    doc_id: str,
    sent_id: int,
    text: str
) -> Dict[str, Any]:
    """
    Run the full extractor pipeline on one sentence.
    Returns the final payload dict (ready for JSON serialization).
    """
    # 1) Cap & stub
    cap_info   = cap_stub(doc_id, sent_id, text)
    # 2) Tokenise
    token_info = tokenise(doc_id, sent_id, cap_info["text_cap"])
    # 3) Dependency parse
    deps_info  = parse_deps(doc_id, sent_id, token_info["tokens"])
    # 3b) Verb-finder gate
    vinfo = verb_finder(doc_id, sent_id, text)
    # 4) Conditional SRL
    frames = [] if vinfo["skip_srl"] else run_srl(doc_id, sent_id, text)
    # 5) Alias resolution
    alias_info = resolve_alias(doc_id, sent_id, frames)
    # 6) Role lookup
    roles_info = lookup_roles(doc_id, sent_id, alias_info["aliases"])
    # 7) Rule-map → raw tuples
    tuples_info = apply_rules(doc_id, sent_id, roles_info["role_ids"])
    # 8) Build nested hulls
    hulls_info  = build_hulls(doc_id, sent_id, tuples_info["tuples"])
    # 9) Post-process into final payload
    payload = post_process(
        doc_id,
        sent_id,
        {
            **cap_info,
            **token_info,
            **deps_info,
            "frames": frames,
            **alias_info,
            **roles_info,
            **tuples_info,
            **hulls_info,
            **vinfo,
        },
    )
    return payload

def extract_doc(
    doc_id: str,
    sentences: List[str]
) -> List[Dict[str, Any]]:
    """
    Apply extract_sentence over all sentences in a document.
    """
    return [
        extract_sentence(doc_id, idx, sent)
        for idx, sent in enumerate(sentences)
    ]

if __name__ == "__main__":
    import json, sys
    # Usage: python cli.py <doc_id> <sent_id> "<sentence>"
    _, doc_id, sent_id, sentence = sys.argv
    result = extract_sentence(doc_id, int(sent_id), sentence)
    print(json.dumps(result, indent=2, ensure_ascii=False))
