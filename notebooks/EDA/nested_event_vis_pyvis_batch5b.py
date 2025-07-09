#!/usr/bin/env python3
"""
PyVis CHV force-graph visualiser • v2.0  (2025-07-04)

▲  What changed vs v1.9
    •  Supports JSON 2 .2  (offsets, meta_local, no evt hub).
    •  Edge-style map simplified → {attr|meta_local: dashed, binder: thick}.
    •  Meta nodes use same green; meta_local edges drawn grey-dashed.
    •  Tooltip now shows UTF-8 offset span when present.
    •  Flag --no-alias hides “(alias: …)” part of SPO labels.
    •  Removed “synthetic SPO→SPO” connectors (evt hubs gone).
"""

import json, argparse, random
from pathlib import Path
from typing import Set, Tuple

import jsonschema, networkx as nx
from pyvis.network import Network

# ── static schema import (unchanged) ─────────────────────────────────────────
from nested_event_vis import SCHEMA          #  still valid – version field bumped

# ── visual style tables ──────────────────────────────────────────────────────
COLORS = {
    "spo":      "#1f77b4",  # blue
    "attr":     "#9e9e9e",  # grey
    "type":     "#ffa94d",  # orange (Type / VerbClass)
    "meta_out": "#2ca02c",  # green
    "chv":      "#8e44ad",  # purple
}
SIZES = { "spo": 26, "attr": 12, "meta_out": 18, "chv": 34 }
BINDER_WIDTH   = 4
DASH_PATTERN   = [5, 3]

# ── helpers ──────────────────────────────────────────────────────────────────
def ingest_json(p: Path) -> Tuple[nx.DiGraph, Set[str]]:
    data = json.loads(p.read_text())
    jsonschema.validate(data, SCHEMA)
    G = nx.DiGraph()
    for nd in data["nodes"]:
        G.add_node(nd["id"], **nd)
    for ed in data["edges"]:
        G.add_edge(ed["source"], ed["target"], kind=ed["kind"])
    sub_spo = {m for hull in data.get("layouts", {}).get("hulls", [])
                     for m in hull.get("members", [])}
    return G, sub_spo

def mk_label(d: dict, hide_alias: bool) -> str:
    roles = "/".join(d.get("roles", []))
    if d["ntype"] == "spo":
        filler = d.get("alias_key", "")
        alias  = "" if hide_alias else f" (alias: {filler})"
        return f"{roles}{alias}"
    else:
        return f"{roles}: {d.get('filler','')}"

def build_pyvis(G: nx.DiGraph,
                sub_spo: Set[str],
                *,
                hide_alias=False,
                seed=4) -> Network:

    random.seed(seed)
    net = Network(height="100vh", width="100vw", directed=True,
                  bgcolor="#f0f4ff", font_color="#000000")
    net.barnes_hut(spring_length=140)

    # ─── nodes ───────────────────────────────────────────────────────────────
    for nid, d in G.nodes(data=True):
        if d["ntype"] == "event":      # event hubs removed in v2.2
            continue

        # colour
        if d["ntype"] == "attr" and any(r in ("Type", "VerbClass") for r in d.get("roles", [])):
            colour = COLORS["type"]
        else:
            colour = COLORS.get(d["ntype"], COLORS["attr"])

        size   = SIZES.get(d["ntype"], 12)
        label  = mk_label(d, hide_alias)
        title  = f"eid_set: {d.get('eid_set', [])}"
        if "offset" in d:                        # show offsets if present
            title += f"<br/>offset: {d['offset']}"
        extra  = {}
        if nid in sub_spo:                      # thick border for hull SPOs
            extra["borderWidth"] = 3

        net.add_node(nid, label=label, color=colour, size=size, title=title, **extra)

    # ─── edges ───────────────────────────────────────────────────────────────
    for u, v, ed in G.edges(data=True):
        if G.nodes[u]["ntype"] == "event" or G.nodes[v]["ntype"] == "event":
            continue                            # no event hubs any more

        kind   = ed.get("kind", "")
        width  = BINDER_WIDTH if kind == "binder" else 1
        dashed = kind in ("attr", "meta_local")

        net.add_edge(u, v, arrows="to", width=width,
                     color="#666" if kind == "meta_local" else None,
                     dashes=DASH_PATTERN if dashed else False)

    # pyvis opts
    net.set_options("""
      {"physics":{"barnesHut":{"springLength":140,"avoidOverlap":1},
       "minVelocity":0.75},"edges":{"smooth":false}}
    """)
    net.heading = "CHV sentence graph"
    return net

# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="CHV force-graph viewer v2.0")
    ap.add_argument("json", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("chv_force.html"))
    ap.add_argument("--no-alias", action="store_true", help="Hide alias_key in SPO labels")
    ap.add_argument("--seed", type=int, default=4)
    args = ap.parse_args()

    G, sub = ingest_json(args.json)
    net    = build_pyvis(G, sub, hide_alias=args.no_alias, seed=args.seed)
    net.write_html(str(args.out), notebook=False)
    print(f"[info] graph written → {args.out}")
