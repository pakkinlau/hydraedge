#!/usr/bin/env python3
"""
PyVis CHV force-graph visualiser · v2.4  (2025-07-05)

Δ vs v2.3-fix1
    · accepts extra edge kinds (e.g. "subevt") without schema edits
    · draws "subevt" edges thin-dashed blue
    · orange border on hull nodes always visible
    · single colour argument → no TypeError
"""

import json, argparse, random, re
from pathlib import Path
from typing import Set, Tuple

import jsonschema, networkx as nx
from   pyvis.network import Network

# ── schema import – we patch its enum at runtime ────────────────────────────
from nested_event_vis import SCHEMA            # your existing file

# ── palette & sizes ─────────────────────────────────────────────────────────
COL = {
    "spo":      "#1f77b4",        # blue
    "attr":     "#9e9e9e",        # grey
    "type":     "#ffa94d",        # orange (Type / VerbClass)
    "meta_out": "#2ca02c",        # green
    "chv":      "#8e44ad"         # purple
}
SIZE        = { "spo": 26, "attr": 12, "meta_out": 18, "chv": 34 }
BINDER_W    = 4
DASH        = [5, 3]
HULL_COLOR  = "#ffa94d"           # orange border

# ── helpers ─────────────────────────────────────────────────────────────────
def _strip_js_comments(txt: str) -> str:
    return re.sub(r"/\*.*?\*/", "", txt, flags=re.S)

def _patch_schema():
    """Add any ad-hoc edge kinds that appear in data but not in the static enum."""
    enum = SCHEMA["properties"]["edges"]["items"]["properties"]["kind"]["enum"]
    for extra in ("subevt",):
        if extra not in enum:
            enum.append(extra)

def ingest_json(p: Path) -> Tuple[nx.DiGraph, Set[str]]:
    _patch_schema()
    data = json.loads(_strip_js_comments(p.read_text(encoding="utf-8")))
    jsonschema.validate(data, SCHEMA)

    G = nx.DiGraph()
    for nd in data["nodes"]:
        G.add_node(nd["id"], **nd)
    for ed in data["edges"]:
        G.add_edge(ed["source"], ed["target"], kind=ed["kind"])

    hull = {m for h in data.get("layouts", {}).get("hulls", [])
              for m in h.get("members", [])}
    return G, hull

def _label(nd: dict, hide_alias: bool) -> str:
    if nd["ntype"] == "spo":
        base = "/".join(nd.get("roles", []))
        return base if hide_alias else f"{base} (alias:{nd.get('alias_key','')})"
    return f"{'/'.join(nd.get('roles', []))}: {nd.get('filler','')}"

def build_pyvis(G: nx.DiGraph,
                hull_nodes: Set[str],
                *,
                hide_alias: bool = False,
                seed: int = 4) -> Network:

    random.seed(seed)
    net = Network("100vh", "100vw", directed=True,
                  bgcolor="#f0f4ff", font_color="#000")
    net.barnes_hut(spring_length=140)

    # ─── nodes ───────────────────────────────────────────────────────────────
    for nid, nd in G.nodes(data=True):
        if nd["ntype"] == "event":            # no event hubs
            continue

        base_colour = (COL["type"] if nd["ntype"] == "attr"
                                      and any(r in ("Type", "VerbClass") for r in nd["roles"])
                       else COL.get(nd["ntype"], COL["attr"]))
        size   = SIZE.get(nd["ntype"], 12)
        label  = _label(nd, hide_alias)
        title  = f"eid_set: {nd.get('eid_set', [])}"
        s, e   = nd.get("char_start", -1), nd.get("char_end", -1)
        if s >= 0 <= e:
            title += f"<br/>offset: {s}‥{e}"

        if nid in hull_nodes:                 # add orange border
            colour = {
                "border": HULL_COLOR,
                "background": base_colour,
                "highlight": {"border": HULL_COLOR,
                              "background": base_colour}
            }
            net.add_node(nid, label=label, size=size, title=title,
                         color=colour, borderWidth=3)
        else:
            net.add_node(nid, label=label, size=size, title=title,
                         color=base_colour)

    # ─── edges ───────────────────────────────────────────────────────────────
    for u, v, ed in G.edges(data=True):
        kind   = ed.get("kind", "")
        width  = BINDER_W if kind == "binder" else 1
        dashed = kind in ("attr", "meta", "subevt")
        colour = "#2ca02c" if kind == "meta" else None   # green for metadata

        net.add_edge(u, v, arrows="to", width=width,
                     color=colour,
                     dashes=DASH if dashed else False)

    # physics
    net.set_options("""{
        "physics":{"barnesHut":{"springLength":140,"avoidOverlap":1},
                   "minVelocity":0.75},
        "edges":{"smooth":false}}""")
    net.heading = "CHV sentence graph (v2.4)"
    return net

# ─── CLI entry ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="CHV force-graph viewer (v2.4)")
    ap.add_argument("json",          type=Path)
    ap.add_argument("-o","--out",    type=Path, default=Path("vis.html"))
    ap.add_argument("--seed",        type=int, default=4)
    ap.add_argument("--no-alias",    action="store_true")
    args = ap.parse_args()

    G, hull = ingest_json(args.json)
    net = build_pyvis(G, hull, hide_alias=args.no_alias, seed=args.seed)
    net.write_html(str(args.out), notebook=False)
    print("✓ graph saved →", args.out.resolve())
