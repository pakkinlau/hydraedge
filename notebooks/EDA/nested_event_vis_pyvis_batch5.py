#!/usr/bin/env python3
"""
PyVis CHV force-graph visualiser · v1.9 (2025-07-04)

• Reads the same JSON schema as nested_event_vis.py
• Builds a force-directed, draggable/zoomable graph (vis.js via PyVis)
• Highlights sub-event SPOs with a thicker border
• Synthesizes direct connectors from main-chain SPOs → sub-event SPOs
• Colours “Type” and “VerbClass” attrs orange; always shows alias_key on SPOs
• Exports to a full-screen HTML file with barnes-hut physics
"""

import json
import argparse
import random
from pathlib import Path
from typing import Set, Tuple

import jsonschema
import networkx as nx
from pyvis.network import Network

from nested_event_vis import SCHEMA  # reuse the static schema & colour defs

# ── style maps ──────────────────────────────────────────────────────────────
COLORS = {
    "spo":      "#1f77b4",
    "attr":     "#9e9e9e",  # general attribute
    "type":     "#ffa94d",  # for Attr nodes with “Type” or “VerbClass” role
    "meta_out": "#2ca02c",
    "chv":      "#8e44ad",
    "event":    "#888888",
}
SIZES = {
    "spo":      25,
    "attr":     12,
    "meta_out": 18,
    "chv":      30,
    "event":    6,
}
HULL_BORDER_WIDTH = 5     # border for sub-event SPOs
SYN_WIDTH = 2
SYN_DASHES = [5, 3]

def ingest_json(p: Path) -> Tuple[nx.DiGraph, Set[str]]:
    """Load & validate JSON, build directed graph, collect sub‐event SPO IDs."""
    data = json.loads(p.read_text(encoding="utf-8"))
    jsonschema.validate(data, SCHEMA)
    G = nx.DiGraph()
    for nd in data["nodes"]:
        G.add_node(nd["id"], **nd)
    for ed in data["edges"]:
        G.add_edge(ed["source"], ed["target"], kind=ed["kind"])
    # gather all SPO IDs that are in any sub-event hull
    subevent_spo: Set[str] = set()
    for hull in data.get("layouts", {}).get("hulls", []):
        subevent_spo.update(hull.get("members", []))
    return G, subevent_spo

def build_pyvis_net(
    G: nx.DiGraph,
    subevent_spo: Set[str],
    *,
    heading: str = "CHV force-graph",
    seed: int = 4,
    include_events: bool = False,
    hide_alias: bool = False
) -> Network:
    """Construct a PyVis Network from our CHV graph."""
    random.seed(seed)
    net = Network(height="100vh", width="100vw", directed=True,
                  bgcolor="#f0f4ff", font_color="#000000")
    net.barnes_hut()

    # ─ add nodes ──────────────────────────────────────────────────────────────
    for node_id, d in G.nodes(data=True):
        # optionally skip event nodes
        if d["ntype"] == "event" and not include_events:
            continue

        # choose colour & size
        # any Attr node with role “Type” or “VerbClass” gets orange
        if d["ntype"] == "attr" and any(r in ("Type", "VerbClass") for r in d.get("roles", [])):
            colour = COLORS["type"]
        else:
            colour = COLORS.get(d["ntype"], COLORS["attr"])
        size = SIZES.get(d["ntype"], 12)

        # build label:
        if d["ntype"] == "event":
            label = ""
        else:
            # SPO nodes: always show alias_key
            # Attr/meta/chv: show role + filler
            if d["ntype"] == "spo":
                # e.g. "Predicate: chase (alias: chase)"
                roles = "/".join(d.get("roles", []))
                filler = d.get("filler", "")
                alias = d.get("alias_key", "")
                label = f"{roles}: {filler} (alias: {alias})"
            else:
                label = f"{'/'.join(d.get('roles', []))}: {d.get('filler','')}"

        title = f"eid_set: {d.get('eid_set', [])}"
        extra = {}
        if d["ntype"] == "spo" and node_id in subevent_spo:
            extra["borderWidth"] = HULL_BORDER_WIDTH

        net.add_node(node_id, label=label, color=colour, size=size,
                     title=title, **extra)

    # ─ add original edges ─────────────────────────────────────────────────────
    for u, v, attrs in G.edges(data=True):
        # skip event‐related edges if events are hidden
        if (G.nodes[u]["ntype"] == "event" or G.nodes[v]["ntype"] == "event") \
           and not include_events:
            continue

        kind = attrs.get("kind", "")
        width = 4 if kind == "binder" else 1
        # dashed for attr/type and event-pred
        dashes = kind in ("attr", "type") or (kind == "event-pred" and [5,5])

        net.add_edge(u, v, arrows="to", width=width, dashes=dashes)

    # ─ synthesize direct SPO→SPO connectors via omitted events ────────────────
    if not include_events:
        for e in G.nodes():
            if G.nodes[e]["ntype"] != "event":
                continue
            inn = [u for u,_,k in G.edges(data="kind") if _ == e and k == "P-O"]
            out = [w for _,w,k in G.edges(data="kind") if _ == e and k == "event-pred"]
            for u in inn:
                for w in out:
                    net.add_edge(u, w, arrows="to",
                                 width=SYN_WIDTH, dashes=SYN_DASHES)

    # ─ physics & styling ───────────────────────────────────────────────────────
    net.set_options("""
    {
      "physics": {
        "barnesHut": { "springLength": 140, "avoidOverlap": 1 },
        "minVelocity": 0.75, "solver": "barnesHut"
      },
      "edges": { "smooth": false }
    }
    """)
    net.heading = heading
    return net

def main():
    ap = argparse.ArgumentParser(description="PyVis CHV force-graph viewer v1.9")
    ap.add_argument("json",     type=Path, help="Path to CHV JSON payload")
    ap.add_argument("-o","--out",type=Path, default=Path("chv_force.html"),
                    help="Output HTML file")
    ap.add_argument("--seed",    type=int, default=4, help="Layout random seed")
    ap.add_argument("--show-events", action="store_true",
                    help="Include ‘event’ nodes in the graph")
    ap.add_argument("--hide-alias", action="store_true",
                    help="Do NOT show `alias_key` on SPO nodes")
    args = ap.parse_args()

    G, subevent_spo = ingest_json(args.json)
    net = build_pyvis_net(
        G,
        subevent_spo,
        seed=args.seed,
        include_events=args.show_events,
        hide_alias=args.hide_alias
    )
    net.write_html(str(args.out), notebook=False)
    print(f"[info] saved → {args.out}")

if __name__ == "__main__":
    main()
