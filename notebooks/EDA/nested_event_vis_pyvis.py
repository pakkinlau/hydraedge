#!/usr/bin/env python3
"""
PyVis CHV force-graph visualiser · v1.6 (2025-07-02)

• Reads the same JSON schema as nested_event_vis.py
• Builds a force-directed, draggable/zoomable graph (vis.js via PyVis)
• Highlights sub-event SPO nodes with a thicker border
• Synthesizes direct connectors from main-chain SPOs → sub-event SPOs
• Colours “Type” attrs orange
• Exports to a full-screen HTML file with barnes-hut physics
"""

from __future__ import annotations
import json
import random
import argparse
from pathlib import Path
from typing import Set, Tuple

import jsonschema
import networkx as nx
from pyvis.network import Network

from nested_event_vis import SCHEMA   # reuse the static schema & colour defs

# ── style maps ──────────────────────────────────────────────────────────────
COLORS = {
    "spo":      "#1f77b4",
    "attr":     "#9e9e9e",
    "type":     "#ffa94d",   # used for attr nodes with “Type” role
    "meta_out": "#2ca02c",
    "chv":      "#8e44ad",
    "event":    "#888888",   # if ever shown
}
SIZES = {
    "spo":      25,
    "attr":     12,
    "meta_out": 18,
    "chv":      30,
    "event":    6,           # tiny
}
# how thick to draw the border around any node in a sub-event hull
HULL_BORDER_WIDTH = 5     
# style for synthesized main→sub-event connectors
SYN_WIDTH = 2
SYN_DASHES = [5, 3]

# ── JSON loader ──────────────────────────────────────────────────────────────
def ingest_json(p: Path) -> Tuple[nx.DiGraph, Set[str]]:
    data = json.loads(p.read_text(encoding="utf-8"))
    jsonschema.validate(data, SCHEMA)
    G = nx.DiGraph()
    for nd in data["nodes"]:
        G.add_node(nd["id"], **nd)
    for ed in data["edges"]:
        G.add_edge(ed["source"], ed["target"], kind=ed["kind"])

    # collect all SPOs that belong to any sub-event hull
    subevent_spo: Set[str] = set()
    for hull in data.get("layouts", {}).get("hulls", []):
        subevent_spo.update(hull.get("members", []))
    return G, subevent_spo

# ── PyVis builder ────────────────────────────────────────────────────────────
def build_pyvis_net(
    G: nx.DiGraph,
    subevent_spo: Set[str],
    *,
    heading: str = "Nested-event CHV graph",
    seed: int = 4,
    include_events: bool = False
) -> Network:
    random.seed(seed)
    net = Network(
        height="100vh", width="100vw", directed=True,
        bgcolor="#f0f4ff", font_color="#000000"
    )
    net.barnes_hut()

    # ─ add nodes ─────────────────────────────────────────────
    for n, d in G.nodes(data=True):
        # skip pure event nodes if desired
        if d["ntype"] == "event" and not include_events:
            continue

        # color & size
        colour = (
            COLORS["type"]
            if d["ntype"] == "attr" and "Type" in d.get("roles", [])
            else COLORS.get(d["ntype"], COLORS["attr"])
        )
        size = SIZES.get(d["ntype"], 12)

        # label only if not an invisible/marker node
        label = ""
        if d["ntype"] != "event":
            label = f"{'/'.join(d.get('roles', []))}: {d.get('filler','')}"

        title = f"eid_set: {d.get('eid_set', [])}"

        # thick border for any SPO in your sub-event hulls
        extra = {}
        if d["ntype"] == "spo" and n in subevent_spo:
            extra["borderWidth"] = HULL_BORDER_WIDTH

        net.add_node(n, label=label, color=colour, size=size, title=title, **extra)

    # ─ add original edges (skipping any that touch omitted events) ─────────
    for u, v, attrs in G.edges(data=True):
        kind = attrs.get("kind", "")
        if not include_events and (G.nodes[u]["ntype"]=="event" or G.nodes[v]["ntype"]=="event"):
            continue
        width = 4 if kind == "binder" else 1
        dashes = {"attr": True, "event-pred": [5,5]}.get(kind, False)
        net.add_edge(u, v, arrows="to", width=width, dashes=dashes)

    # ─ synthesize direct SPO→SPO connectors via each omitted event ──────────
    if not include_events:
        for e in G.nodes():
            if G.nodes[e]["ntype"] != "event":
                continue
            # any spo→event via P-O
            inn = [u for u,v,k in G.edges(data="kind") if v==e and k=="P-O"]
            # any event→spo via event-pred
            out = [w for u,w,k in G.edges(data="kind") if u==e and k=="event-pred"]
            for u in inn:
                for w in out:
                    net.add_edge(u, w,
                                 arrows="to",
                                 width=SYN_WIDTH,
                                 dashes=SYN_DASHES)

    # ─ override physics & smoothing ────────────────────────────────────────
    net.set_options("""
    {
      "physics": {
        "barnesHut": {
          "springLength": 140,
          "avoidOverlap": 1
        },
        "minVelocity": 0.75,
        "solver": "barnesHut"
      },
      "edges": {
        "smooth": false
      }
    }
    """)
    net.heading = heading
    return net

# ── CLI entry point ──────────────────────────────────────────────────────────
def _cli():
    ap = argparse.ArgumentParser(description="PyVis CHV force-graph viewer")
    ap.add_argument("json", type=Path, help="Path to CHV JSON payload")
    ap.add_argument(
        "-o","--out", type=Path,
        default=Path("chv_force.html"),
        help="Output HTML file"
    )
    ap.add_argument(
        "--seed", type=int, default=4,
        help="Random seed for layout"
    )
    ap.add_argument(
        "--show-events", action="store_true",
        help="Include tiny ‘event’ nodes in the graph"
    )
    args = ap.parse_args()

    G, subevent_spo = ingest_json(args.json)
    net = build_pyvis_net(
        G,
        subevent_spo,
        seed=args.seed,
        include_events=args.show_events
    )
    net.write_html(str(args.out), notebook=False)
    print(f"[info] saved → {args.out}")

if __name__ == "__main__":
    _cli()
