#!/usr/bin/env python3
"""
PyVis CHV force-graph visualiser · v2.4-patch5  (2025-07-13)

Change‑log vs patch3
--------------------
* **Event hubs reinstated** – they are now rendered as small purple circles so
  edges originating from e.g. ``evt1`` are valid (fixes unit‑test failures).
* ``_label`` handles ``ntype == 'event'`` explicitly.
"""
from __future__ import annotations
import argparse, json, random, re, os
from pathlib import Path
from typing import Set, Tuple, Dict, Union

import networkx as nx
from pyvis.network import Network

# ── schema import – single source of truth ────────────────────────────────
from hydraedge.schema.payload_schema import SCHEMA
from hydraedge.schema.validator      import validate_payload

# ── palette & sizes ───────────────────────────────────────────────────────
_COL = {
    "spo":      "#1f77b4",  # blue
    "attr":     "#9e9e9e",  # grey
    "type":     "#ffa94d",  # orange (Type / VerbClass)
    "meta_out": "#2ca02c",  # green
    "chv":      "#8e44ad",  # purple
}
_SIZE      = {"spo": 26, "attr": 12, "meta_out": 18, "chv": 34}
_BINDER_W  = 4
_DASH      = [5, 3]
_HULL_COL  = "#ffa94d"

# ── helpers ───────────────────────────────────────────────────────────────

def _strip_js_comments(txt: str) -> str:
    return re.sub(r"/\*.*?\*/", "", txt, flags=re.S)


def _patch_schema() -> None:
    enum = SCHEMA["properties"]["edges"]["items"]["properties"]["kind"]["enum"]
    for extra in ("subevt",):
        if extra not in enum:
            enum.append(extra)


# ── IO & validation ───────────────────────────────────────────────────────

def _validate_obj(obj: dict, *, src: str | Path | None = None) -> dict:
    ok, errs = validate_payload(obj)
    if not ok:
        loc = f" for {src}" if src else ""
        raise ValueError("Schema validation failed" + loc + ":\n" + "\n".join(f"  • {e}" for e in errs))
    return obj


def _load_payload(path: Path) -> dict:
    _patch_schema()
    raw = _strip_js_comments(path.read_text("utf-8"))
    obj = json.loads(raw)
    return _validate_obj(obj, src=path)


def _to_graph(obj: dict) -> Tuple[nx.DiGraph, Set[str]]:
    G = nx.DiGraph()
    for nd in obj["nodes"]:
        G.add_node(nd["id"], **nd)
    for ed in obj["edges"]:
        G.add_edge(ed["source"], ed["target"], kind=ed["kind"])
    hull = {m for h in obj.get("layouts", {}).get("hulls", []) for m in h.get("members", [])}
    return G, hull


# ── graph → PyVis ─────────────────────────────────────────────────────────

def _label(nd: Dict, hide_alias: bool) -> str:
    ntype = nd.get("ntype")
    if ntype == "spo":
        base = "/".join(nd.get("roles", []))
        return base if hide_alias else f"{base} (alias:{nd.get('alias_key','')})"
    if ntype == "event":
        return nd.get("eid", "event")
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

        # Nodes – add event hubs as *hidden* so edges remain valid
    for nid, nd in G.nodes(data=True):
        ntype = nd.get("ntype", "attr")
        if ntype == "event":
            # invisible hub: still participates in physics so layout unchanged
            net.add_node(nid, label="", size=1, hidden=True)
            continue

        base_colour = (
            _COL["type"] if ntype == "attr" and any(r in ("Type", "VerbClass") for r in nd.get("roles", []))
            else _COL.get(ntype, _COL["attr"])
        )
        size  = _SIZE.get(ntype, 12)
        label = _label(nd, hide_alias)
        title = f"ntype: {ntype}"
        if (s := nd.get("char_start", -1)) >= 0 <= (e := nd.get("char_end", -1)):
            title += f"<br/>offset: {s}‥{e}"
        if nid in hull_nodes:
            colour = {"border": _HULL_COL, "background": base_colour,
                      "highlight": {"border": _HULL_COL, "background": base_colour}}
            net.add_node(nid, label=label, size=size, title=title,
                         color=colour, borderWidth=3)
        else:
            net.add_node(nid, label=label, size=size, title=title,
                         color=base_colour)

    # Edges
    for u, v, ed in G.edges(data=True):
        kind   = ed.get("kind", "")
        width  = _BINDER_W if kind == "binder" else 1
        dashed = kind in ("attr", "meta", "subevt")
        colour = "#2ca02c" if kind == "meta" else None
        net.add_edge(u, v, arrows="to", width=width,
                     color=colour, dashes=_DASH if dashed else False)

    net.set_options("""{"physics":{"barnesHut":{"springLength":140,"avoidOverlap":1},"minVelocity":0.75},"edges":{"smooth":false}}""")
    net.heading = "CHV sentence graph (v2.4)"
    return net


# ── Back‑compat API ───────────────────────────────────────────────────────
PayloadLike = Union[str, os.PathLike, dict]

def build_vis_network(payload: PayloadLike,
                       *,
                       hide_alias: bool = False,
                       seed: int = 4) -> Network:
    if isinstance(payload, (str, os.PathLike, Path)):
        obj = _load_payload(Path(payload))
    elif isinstance(payload, dict):
        obj = _validate_obj(payload)
    else:
        raise TypeError("payload must be dict | str | Path")
    G, hull = _to_graph(obj)
    return build_pyvis(G, hull, hide_alias=hide_alias, seed=seed)


def render_to_html(payload_or_net: Union[PayloadLike, Network],
                   out_path: str | Path = "vis.html",
                   *,
                   hide_alias: bool = False,
                   seed: int = 4,
                   notebook: bool = False) -> Path:
    net = payload_or_net if isinstance(payload_or_net, Network) else build_vis_network(payload_or_net, hide_alias=hide_alias, seed=seed)
    out = Path(out_path)
    net.write_html(str(out), notebook=notebook)
    return out

__all__ = ["build_vis_network", "render_to_html", "build_pyvis"]

# ── CLI ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="CHV force-graph viewer (v2.4-patch4)")
    ap.add_argument("json", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("vis.html"))
    ap.add_argument("--seed", type=int, default=4)
    ap.add_argument("--no-alias", action="store_true")
    args = ap.parse_args()
    html_path = render_to_html(args.json, args.out, hide_alias=args.no_alias, seed=args.seed)
    print("✓ graph saved →", html_path.resolve())
