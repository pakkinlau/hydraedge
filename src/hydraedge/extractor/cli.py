# src/hydraedge/extractor/cli.py

"""
Command-line API for the HydraEdge extractor pipeline (WP1–WP9).
Provides two entry points:
  • extract_sentence():        returns the final JSON payload
  • extract_sentence_debug():  returns a dict of all intermediate stages + final payload
"""

import uuid
from pathlib import Path
from typing import Any, Dict, List

from .wp1_cap_stub   import cap_and_stub
from .wp2_tokenise   import tokenise_pos
from .wp3_dependency import dependency_arcs
from .wp4_srl        import srl_spans
from .wp5_alias      import AliasResolver
from .wp6_roles      import RoleLibrary
from .wp7_rulemap    import map_role
from .wp8_hull       import hullify
from .wp9_post       import merge_spans


def extract_sentence_debug(
    sentence: str,
    gaz_path: str,
    role_path: str,
) -> Dict[str, Any]:
    """
    Run the full pipeline on one sentence, returning a dict with keys:
      cap, tokens, deps, frames, raw, tuples, hulls, payload
    """
    debug: Dict[str, Any] = {}

    # 1 · CAP & stub
    cap = cap_and_stub(sentence)
    debug["cap"] = cap

    # 2 · tokens + POS
    tokens = tokenise_pos(cap["text"])
    debug["tokens"] = tokens

    # 3 · dependency arcs (pass the string, not the token list)
    deps = dependency_arcs(cap["text"])
    debug["deps"] = deps

    # 4 · SRL frames
    frames = srl_spans(cap["text"])
    debug["frames"] = frames

    # 5 · raw tuple extraction (before alias/role mapping)
    raw: List[Dict[str, Any]] = []
    for frame in frames:
        for i, tag in enumerate(frame["tags"]):
            if tag.startswith("B-") and tag != "B-V":
                raw.append({
                    "srl" : tag[2:],                     # e.g. "ARG0", "TMP", etc.
                    "span": frame["words"][i],           # the token text
                    "verb": frame["verb"],               # the surface verb
                    "eid" : frame["description"].split("[", 1)[0],
                })
    debug["raw"] = raw

    # 6 · alias + learned rule-map → internal role keys
    alias_res = AliasResolver(Path(gaz_path))
    role_lib  = RoleLibrary(Path(role_path))

    tuples: List[Dict[str, Any]] = []
    for r in raw:
        span_key = alias_res.resolve(r["span"])
        # find the dependency label for this event:
        #   r["eid"] is like "e0", so take the numeric part
        idx = int(r["eid"][1:]) if r["eid"].startswith("e") and r["eid"][1:].isdigit() else 0
        dep_label = deps[idx][2]

        role_key = map_role(r["srl"], dep_label, r["verb"], span_key)
        # (we drop the old role_lib.get_vector check;
        #  encoding will blow up if role_key is missing)

        tuples.append({"role": role_key, "span": span_key, "eid": r["eid"]})
    debug["tuples"] = tuples

    # 7 · hulls (nested event grouping)
    hulls = hullify(tuples)
    debug["hulls"] = hulls

    # 8 · assemble final payload (with post-merge)
    final_tuples = merge_spans(tuples)
    payload = {
        "version" : "2.4",
        "sentence": sentence,
        "id"      : str(uuid.uuid4()),
        "tuples"  : final_tuples,
        "layouts" : {"hulls": hulls},
    }
    debug["payload"] = payload

    return debug


def extract_sentence(
    sentence: str,
    gaz_path: str,
    role_path: str,
) -> Dict[str, Any]:
    """
    Run the full pipeline and return only the final JSON payload.
    """
    return extract_sentence_debug(sentence, gaz_path, role_path)["payload"]


def extract_doc(
    sentences: List[str],
    gaz_path: str,
    role_path: str,
) -> List[Dict[str, Any]]:
    """
    Run extract_sentence on each sentence in a document.
    Returns list of payloads.
    """
    return [
        extract_sentence(s, gaz_path, role_path)
        for s in sentences
    ]
