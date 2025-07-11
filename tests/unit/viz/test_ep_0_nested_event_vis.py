###########################
# File: tests/unit/viz/test_ep_0_nested_event_vis.py
###########################
"""Unit-tests for the nested-event visualiser."""
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from hydraedge.viz.ep_0_nested_event_vis import build_vis_network, render_to_html

SAMPLE = Path("data/sample-record-data-graph/example_payload_schema_2.4.json")


@pytest.mark.parametrize("hide_alias", [False, True])
def test_build_vis_network_smoke(hide_alias: bool):
    """The builder returns ≥1 node and ≥1 edge without crashing."""
    import json, re

    payload = SAMPLE.read_text(encoding="utf-8")
    obj = json.loads(re.sub(r"/\*.*?\*/", "", payload, flags=re.S))
    net = build_vis_network(obj, hide_alias=hide_alias)

    assert len(net.nodes) > 0, "No nodes produced"
    assert len(net.edges) > 0, "No edges produced"


def test_render_to_html(tmp_path: Path):
    """End-to-end render writes a non-trivial HTML file with a #mynetwork div."""
    out = tmp_path / "graph.html"
    render_to_html(SAMPLE, out, hide_alias=True)

    assert out.exists() and out.stat().st_size > 1_000, "HTML too small"
    soup = BeautifulSoup(out.read_text(encoding="utf-8"), "html.parser")
    assert soup.find("div", {"id": "mynetwork"}) is not None, "vis container missing"
