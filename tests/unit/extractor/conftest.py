# tests/unit/extractor/conftest.py

import pathlib
import os

# ── Create minimal artefacts at project root ───────────────────────────────────
project_root = pathlib.Path(__file__).parents[3]  # ../../../.. → your repo root

# 1) syn_dict.tsv with just “google” and “youtube” as keys
syn_path = project_root / "syn_dict.tsv"
if not syn_path.exists():
    syn_path.write_text(
        "google\n"
        "youtube\n",
        encoding="utf-8"
    )

# 2) roles.tsv with AGENT and PATIENT
roles_path = project_root / "roles.tsv"
if not roles_path.exists():
    roles_path.write_text(
        "AGENT\t11111111\n"
        "PATIENT\t22222222\n",
        encoding="utf-8"
    )

# ── Now load all the fixtures ──────────────────────────────────────────────────
import json, hashlib, pytest

from hydraedge.extractor.wp1_cap_stub import cap_and_stub
from hydraedge.extractor.wp2_tokenise import tokenise_pos
from hydraedge.extractor.wp3_dependency import dependency_arcs
from hydraedge.extractor.wp4_srl import srl_spans
from hydraedge.extractor.wp5_alias import AliasResolver
from hydraedge.extractor.wp6_roles import RoleLibrary
from hydraedge.extractor.wp7_rulemap import map_role
from hydraedge.extractor.wp8_hull import hullify
from hydraedge.extractor.wp9_post import merge_spans
from hydraedge.extractor.cli import extract_sentence

# ── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def sample_sentence() -> str:
    return "In 2006 Google acquired YouTube for $1.65 billion."

@pytest.fixture(scope="session")
def cap_result(sample_sentence):
    return cap_and_stub(sample_sentence)

@pytest.fixture(scope="session")
def tokens(cap_result):
    return tokenise_pos(cap_result["text"])

@pytest.fixture(scope="session")
def deps(cap_result):
    return dependency_arcs(cap_result["text"])

@pytest.fixture(scope="session")
def srl_frames(cap_result):
    return srl_spans(cap_result["text"])

@pytest.fixture(scope="session")
def first_frame(srl_frames):
    return srl_frames[0] if srl_frames else None

# instantiate the singletons exactly as cli.py does
_ALIAS = AliasResolver(syn_path)
_ROLES = RoleLibrary(roles_path)

@pytest.fixture(scope="session")
def tuples_result(first_frame, deps):
    if first_frame is None:
        return []
    tuples = []
    tags  = first_frame["tags"]
    words = first_frame["words"]
    for i_tok, tag in enumerate(tags):
        if tag.startswith("B-ARG"):
            role = tag[2:]            # strip "B-"
            dep  = deps[i_tok][2]
            internal = map_role(role, dep)
            alias = _ALIAS.resolve(words[i_tok])
            tuples.append({"role": internal, "span": alias, "eid": "e0"})
    return merge_spans(tuples)

@pytest.fixture(scope="session")
def hulls(tuples_result):
    return hullify(tuples_result)

@pytest.fixture(scope="session")
def payload(sample_sentence):
    return extract_sentence(sample_sentence)

def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()

pytest._hydra_hash = _hash
