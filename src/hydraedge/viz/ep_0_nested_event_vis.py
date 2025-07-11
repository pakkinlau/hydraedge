###########################
# File: src/hydraedge/viz/ep_0_nested_event_vis.py
###########################
"""
HydraEdge nested-event visualiser (schema ≥ 2.4)

* Reads a single extracted-JSON payload.
* Validates it with the shared `hydraedge.schema.SCHEMA`.
* Builds an interactive force-directed graph via **pyvis**.
* Writes a self-contained HTML file (optionally wrapped in a template).

CLI
~~~
python -m hydraedge.viz.ep_0_nested_event_vis \
       data/sample-record-data-graph/example_payload_schema_2.4.json \
       -o demo.html --no-alias
"""
from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Dict, Set, Tuple

import jsonschema
import networkx as nx
from pyvis.network import Network

# -----------------------------------------------------------------------------
# 0 ▸ load the *single* shared schema object
# -----------------------------------------------------------------------------
try:
    from hydraedge.schema import SCHEMA
except ImportError as exc:
    raise RuntimeError("hydraedge.schema.SCHEMA missing!") from exc

###############################################################################
# 1 ▸ constants                                                               #
###############################################################################
_COLORS: Dict[str, str] = {
    "spo":      "#1f77b4",    # blue
    "attr":     "#9e9e9e",    # grey
    "meta_out": "#2ca02c",    # green
    "chv":      "#8e44ad",    # purple
    "type":     "#ffa94d",    # orange (Type / VerbClass)
}
_SIZE      = {"spo": 26, "attr": 12, "meta_out": 18, "chv": 34}
_DASH      = [5, 3]
_HULL_EDGE = "#ffa94d"
_BINDER_W  = 4
_JSON_CMT  = re.compile(r"/\*.*?\*/", re.S)

_CORE_KINDS = {"attr", "binder", "meta", "subevt"}

###############################################################################
# 2 ▸ schema guard / patcher                                                  #
###############################################################################
def _ensure_enum_path() -> list:
    props  = SCHEMA.setdefault("properties", {})
    edges  = props.setdefault("edges", {})
    items  = edges.setdefault("items", {})
    eprops = items.setdefault("properties", {})
    kind   = eprops.setdefault("kind", {})
    return kind.setdefault("enum", [])

def _patch_schema(payload: dict) -> None:
    enum = _ensure_enum_path()
    # include core + any kinds actually present
    for k in _CORE_KINDS | {e.get("kind", "") for e in payload.get("edges", [])}:
        if k and k not in enum:
            enum.append(k)

###############################################################################
# 3 ▸ build helpers                                                           #
###############################################################################
def _load_json(path: Path) -> dict:
    txt = _JSON_CMT.sub("", path.read_text(encoding="utf-8"))
    return json.loads(txt)

def _build_nx(payload: dict) -> Tuple[nx.DiGraph, Set[str]]:
    # allow the schema to accept any edge-kind we see
    _patch_schema(payload)
    jsonschema.validate(payload, SCHEMA)

    G = nx.DiGraph()
    # first, register *all* nodes (including structural "event" hubs)
    for nd in payload["nodes"]:
        G.add_node(nd["id"], **nd)
    # then edges
    for ed in payload["edges"]:
        G.add_edge(ed["source"], ed["target"], kind=ed["kind"])

    hull = {
        member
        for h in payload.get("layouts", {}).get("hulls", [])
        for member in h.get("members", [])
    }
    return G, hull

def _label(nd: dict, hide_alias: bool) -> str:
    if nd["ntype"] == "spo":
        base = "/".join(nd.get("roles", []))
        return base if hide_alias else f"{base}\n(alias:{nd.get('alias_key','')})"
    if nd["ntype"] == "attr":
        role   = nd.get("roles", ["attr"])[0]
        filler = str(nd.get("filler", ""))[:14]
        return f"{role}:{filler}"
    return nd.get("ntype", nd["id"])

def _add_nodes(net: Network, G: nx.DiGraph, hull: Set[str], hide_alias: bool) -> None:
    for nid, nd in G.nodes(data=True):
        if nd["ntype"] == "event":
            # structural hubs must still be present in net.get_nodes(),
            # but rendered invisible so edges can attach.
            net.add_node(nid, hidden=True)
            continue

        base_col = (
            _COLORS["type"]
            if nd["ntype"] == "attr" and {"Type","VerbClass"} & set(nd.get("roles",[]))
            else _COLORS.get(nd["ntype"], "#cccccc")
        )
        kw = dict(
            label=_label(nd, hide_alias),
            title=json.dumps({k: v for k,v in nd.items() if k not in {"id","alias_key"}},
                              ensure_ascii=False),
            size=_SIZE.get(nd["ntype"], 14),
        )
        if nid in hull:
            kw["color"] = {
                "background": base_col,
                "border":     _HULL_EDGE,
                "highlight":  {"background": base_col, "border": _HULL_EDGE},
            }
            kw["borderWidth"] = 3
        else:
            kw["color"] = base_col

        net.add_node(nid, **kw)

def _add_edges(net: Network, G: nx.DiGraph) -> None:
    for u,v,ed in G.edges(data=True):
        kind = ed.get("kind","")
        net.add_edge(
            u, v,
            arrows="to",
            width=_BINDER_W if kind=="binder" else 1,
            color="#2ca02c" if kind=="meta" else None,
            dashes=_DASH if kind in _CORE_KINDS else False,
        )

def build_vis_network(payload: dict, *, hide_alias: bool=False, seed: int=4) -> Network:
    """Return a fully-configured pyvis.Network."""
    random.seed(seed)
    G, hull = _build_nx(payload)

    net = Network(height="100vh", width="100vw", bgcolor="#f0f4ff", directed=True)
    net.barnes_hut(spring_length=140)

    _add_nodes(net, G, hull, hide_alias)
    _add_edges(net, G)

    net.set_options('{"physics":{"barnesHut":{"springLength":140}},"edges":{"smooth":false}}')
    net.heading = "HydraEdge CHV graph"
    return net

def render_to_html(
    json_path: Path,
    out_path:  Path,
    *,
    template: Path|None = None,
    hide_alias: bool    = False,
    seed:       int     = 4,
) -> None:
    """Load JSON, build network, write out HTML (optionally wrapping a template)."""
    payload = _load_json(json_path)
    net     = build_vis_network(payload, hide_alias=hide_alias, seed=seed)

    if template and template.exists():
        net.template = template.read_text(encoding="utf-8")
    net.write_html(str(out_path), notebook=False)

###############################################################################
# 4 ▸ CLI                                                                     #
###############################################################################
def _cli() -> None:
    ap = argparse.ArgumentParser(description="Nested-event graph visualiser")
    ap.add_argument("json",      type=Path, help="Extracted-JSON payload (schema ≥ 2.4)")
    ap.add_argument("-o","--out",type=Path, default=Path("vis.html"), help="Output HTML file")
    ap.add_argument("--template",type=Path,                     help="Optional HTML template")
    ap.add_argument("--seed",    type=int,     default=4,       help="Layout RNG seed")
    ap.add_argument("--no-alias",action="store_true",          help="Hide alias keys")
    args = ap.parse_args()

    render_to_html(
        args.json, args.out,
        template   = args.template,
        hide_alias = args.no_alias,
        seed       = args.seed,
    )
    print("✓ graph written →", args.out.resolve())

if __name__=="__main__":
    _cli()
