import pathlib
from hydraedge.extractor import wp6_roles

# --------------------------------------------------------------------------- #
#                         Helper to forge a mini state                        #
# --------------------------------------------------------------------------- #
ROLE_PATH = pathlib.Path("roles.tsv") # adjust if needed


def _state_with_roles(labels):
    """return pipeline state stub with frames containing given labels."""
    frames = [
        {
            "verb": "eat",
            "arguments": [{"label": lab, "span": [0, 1]} for lab in labels],
        }
    ]
    return {"frames": frames, "doc_id": "docX", "sent_id": 0}


# --------------------------------------------------------------------------- #
#                                    Tests                                    #
# --------------------------------------------------------------------------- #
def test_all_roles_known():
    st = _state_with_roles(["ARG0", "ARG1"])
    out = wp6_roles.run(st, role_path=ROLE_PATH)
    assert out["roles_ok"] is True
    assert out["meta"]["unseen_roles"] == []


def test_unseen_role_caught():
    st = _state_with_roles(["ARG0", "ARGQ"])  # ARGQ is fictitious
    out = wp6_roles.run(st, role_path=ROLE_PATH)
    assert out["roles_ok"] is False
    assert out["meta"]["unseen_roles"] == ["ARGQ"]
