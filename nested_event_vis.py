#!/usr/bin/env python3
"""
Nested-event CHV visualiser · v19  (2025-07-02, “fan-out attr” patch)

Changes v18 → v19
• Two-phase layout:
    1. Freeze positions of non-attr + orange “Type” attr nodes.
    2. Place remaining grey attribute nodes on an outer ring,
       always outside the convex hull of a sub-event triangle.
• Result: clearer hull, fewer edge crossings.
"""

from __future__ import annotations
import argparse, json, math, random
from pathlib import Path
from typing import Dict, List, Tuple

import jsonschema
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.patches import Polygon
from matplotlib.path import Path as MplPath

# ───────────────────────────── 1 · JSON schema ─────────────────────────────
SCHEMA: Dict = {  # (unchanged; see v18 for contents)
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Nested-event CHV graph",
    "type": "object",
    "required": ["version", "sentence", "nodes", "edges"],
    "properties": {
        "version":  {"type": "string"},
        "sentence": {"type": "string"},
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "filler", "roles", "eid_set", "ntype"],
                "properties": {
                    "id":      {"type": "string"},
                    "filler":  {"type": "string"},
                    "roles":   {"type": "array", "items": {"type": "string"}},
                    "eid_set": {"type": "array", "items": {"type": "string"}},
                    "ntype":   {"enum": ["spo", "attr", "meta_out",
                                         "chv", "event"]}
                }
            }
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source", "target", "kind"],
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "kind":   {"enum": ["S-P", "P-O", "attr",
                                        "meta", "binder", "event-pred"]}
                }
            }
        },
        "layouts": {
            "type": "object",
            "properties": {
                "hulls": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["members"],
                        "properties": {
                            "eid": {"type": "string"},
                            "members": {"type": "array",
                                        "items": {"type": "string"}}
                        }
                    }
                }
            }
        }
    }
}


def ingest_json(p: Path):
    data = json.loads(p.read_text("utf-8"))
    jsonschema.validate(data, SCHEMA)
    G = nx.DiGraph()
    for nd in data["nodes"]:
        G.add_node(nd["id"], **nd)
    for ed in data["edges"]:
        G.add_edge(ed["source"], ed["target"], kind=ed["kind"])
    return G, data.get("layouts", {}), data["sentence"]

# ───────────────────────────── 2 · Style tables ────────────────────────────
COLOR_SPO        = "#1f77b4"
COLOR_ATTR       = (0.45, 0.45, 0.45, 0.35)
COLOR_TYPE_ATTR  = "#ffa94d"        # orange
COLOR_META       = "#2ca02c"
COLOR_CHV        = "#8e44ad"
COLOR_EVENT_FILL = "#ffffff00"      # transparent

NODE_SIZE = {
    "spo": 880,
    "attr": 420,
    "meta_out": 700,
    "chv": 1100,
    "event": 500
}

EDGE_STYLE = {
    "S-P":        dict(width=2.6, style="solid",  arrows=True,  arrowsize=17),
    "P-O":        dict(width=2.6, style="solid",  arrows=True,  arrowsize=17),
    "attr":       dict(width=1.3, style="dotted", arrows=False),
    "meta":       dict(width=1.3, style="dotted", arrows=True,  arrowsize=13),
    "binder":     dict(width=4.0, style="solid",  arrows=True,  arrowsize=17),
    "event-pred": dict(width=2.6, style="dashed", arrows=True,
                       arrowstyle="-|>", arrowsize=15)
}

CHV_LINEWIDTH = 2.5

# ───────────────────────── 3 · Geometry helpers ────────────────────────────
def convex_hull(pts: List[Tuple[float, float]]):
    if len(pts) < 4:
        return pts
    pts = sorted({tuple(map(float, p)) for p in pts})
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) > 1 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) > 1 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def _push_apart(pos: Dict[str, np.ndarray], nodes: List[str],
                *, d_min=0.28, max_iter=25):
    for _ in range(max_iter):
        moved = False
        for i, a in enumerate(nodes):
            for b in nodes[i+1:]:
                v = pos[b] - pos[a]
                d = np.linalg.norm(v)
                if 1e-6 < d < d_min:
                    shift = 0.5 * (d_min - d) * v / d
                    pos[a] -= shift
                    pos[b] += shift
                    moved = True
        if not moved:
            break
    return pos

# ───────────────────────────── 4 · Renderer ────────────────────────────────
def _node_style(data):
    if data["ntype"] == "spo":
        return COLOR_SPO, NODE_SIZE["spo"]
    if data["ntype"] == "meta_out":
        return COLOR_META, NODE_SIZE["meta_out"]
    if data["ntype"] == "chv":
        return COLOR_CHV, NODE_SIZE["chv"]
    if data["ntype"] == "event":
        return COLOR_EVENT_FILL, NODE_SIZE["event"]
    if "Type" in data.get("roles", []):
        return COLOR_TYPE_ATTR, NODE_SIZE["attr"]
    return COLOR_ATTR, NODE_SIZE["attr"]


def draw_graph(ax, G, sentence, layouts=None, *, seed=4):
    rnd = random.Random(seed ^ 0xBEEF)
    # Phase 0 · spring layout on ALL nodes
    pos = nx.spring_layout(G, seed=seed,
                           k=1.1 / math.sqrt(len(G)), iterations=250)
    # Tiny jitter
    for n in pos:
        pos[n] += 0.03 * np.array([rnd.uniform(-1, 1), rnd.uniform(-1, 1)])

    # Build node lists
    spo   = [n for n in G if G.nodes[n]["ntype"] == "spo"]
    attr  = [n for n in G if G.nodes[n]["ntype"] == "attr"]
    meta  = [n for n in G if G.nodes[n]["ntype"] == "meta_out"]
    evt   = [n for n in G if G.nodes[n]["ntype"] == "event"]
    CHV   = next(n for n in G if G.nodes[n]["ntype"] == "chv")

    # Phase 1 · freeze core nodes
    pos = _push_apart(pos, spo, d_min=0.32)
    centroid = np.mean([pos[n] for n in spo], axis=0)
    pos[CHV] = centroid + np.array([0.0, 0.7])
    for i, m in enumerate(meta):
        ang = i * 2 * math.pi / max(1, len(meta))
        pos[m] = pos[CHV] + 0.7 * np.array([math.cos(ang), math.sin(ang)])

    # Optional hull (first layout)
    hull_cfg = layouts.get("hulls", [])
    hull = hull_path = None
    if hull_cfg:
        members = hull_cfg[0]["members"]
        hull_pts = [pos[m] for m in members if m in pos]
        if len(hull_pts) >= 3:
            hull = convex_hull(hull_pts)
            hull_path = MplPath(hull)

    # Extract orange “Type” nodes (treated as frozen anchors)
    type_attr = [n for n in attr if "Type" in G.nodes[n]["roles"]]
    frozen = set(spo + meta + evt + type_attr + [CHV])

    # Phase 2 · re-place grey attribute nodes outside hull / radial ring
    grey_attr = [n for n in attr if n not in type_attr]
    r_base = 0.52  # base distance from parent
    if hull:
        hull_centre = np.mean(hull, axis=0)
        # distance from centre to hull edge
        hull_radius = max(np.linalg.norm(p - hull_centre) for p in hull)
    for s in spo:
        kids = [a for a in grey_attr if (s, a) in G.edges and
                G.edges[s, a]["kind"] == "attr"]
        if not kids:
            continue
        k = len(kids)
        base_ang = rnd.uniform(0, 2 * math.pi)
        for j, a in enumerate(kids):
            ang = base_ang + j * 2 * math.pi / k
            r = r_base
            if hull and hull_path.contains_point(pos[a]):
                r = hull_radius + 0.25
            pos[a] = pos[s] + r * np.array([math.cos(ang), math.sin(ang)])

    # Mild push-apart between attributes
    pos = _push_apart(pos, grey_attr, d_min=0.26)

    # Phase 3 · draw
    lw = [CHV_LINEWIDTH if n == CHV else 1.0 for n in G]
    nx.draw_networkx_nodes(
        G, pos,
        node_size=[_node_style(G.nodes[n])[1] for n in G],
        node_color=[_node_style(G.nodes[n])[0] for n in G],
        edgecolors="black", linewidths=lw, ax=ax)

    def fmt(s: str) -> str:
        return ":\n".join(s.split(":", 1)) if ":" in s else s
    labels = {n: fmt(f'{" / ".join(sorted(G.nodes[n]["roles"]))}:{G.nodes[n]["filler"]}')
              for n in G if G.nodes[n]["ntype"] != "event"}
    nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=ax)

    for kind, sty in EDGE_STYLE.items():
        edges = [(u, v) for u, v in G.edges if G.edges[u, v]["kind"] == kind]
        if not edges:
            continue
        nx.draw_networkx_edges(
            G, pos, edgelist=edges,
            style=sty["style"], width=sty["width"],
            edge_color="black",
            arrows=sty.get("arrows", True),
            arrowstyle="-|>" if sty.get("arrows", True) else "-",
            arrowsize=sty.get("arrowsize", 17),
            ax=ax)

    if hull:
        ax.add_patch(
            Polygon(hull, closed=True,
                    facecolor=(0.80, 0.88, 1.0, 0.15),
                    edgecolor=(0.25, 0.55, 1.0, 0.75),
                    linewidth=2, linestyle="--", zorder=0))
        cx, cy = np.mean(hull, axis=0)
        ax.text(cx, cy, hull_cfg[0].get("eid", "sub-event"),
                ha="center", va="center", fontsize=9)

    ax.set_title("Nested-event graph with CHV node", fontsize=13, pad=12)
    ax.axis("off")
    ax.text(0.5, -0.08, f"Sentence:\n{sentence}", transform=ax.transAxes,
            ha="center", va="top", fontsize=9)

# ───────────────────────────── 5 · CLI wrapper ─────────────────────────────
def _cli():
    ap = argparse.ArgumentParser(description="Render nested-event graph from JSON.")
    ap.add_argument("json", type=Path)
    ap.add_argument("-o", "--out", type=Path, help="output PNG/SVG")
    ap.add_argument("--seed", type=int, default=4)
    ap.add_argument("--no-show", action="store_true")
    args = ap.parse_args()

    G, layouts, sent = ingest_json(args.json)
    fig, ax = plt.subplots(figsize=(8, 9))
    draw_graph(ax, G, sent, layouts, seed=args.seed)
    fig.tight_layout()
    if args.out:
        fig.savefig(args.out, dpi=300, bbox_inches="tight")
        print(f"[info] saved → {args.out}")
    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    _cli()
