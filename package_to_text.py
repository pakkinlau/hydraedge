#!/usr/bin/env python3
"""
package_to_text.py – dump a project into plain-text
===================================================
Produces a **two-part** text report of the directory containing this script:
1. **ASCII tree** (Part 1) – directory structure with extensive, pattern-based
   exclusion rules that avoid build artefacts, caches, backups, etc.
2. **Flat listing** (Part 2) – every file that survives the filters, with full
   contents.  Jupyter notebooks are included **sans outputs / attachments** so
   that embedded base-64 images are never emitted.
The combined text is copied to the clipboard (best-effort via *pyperclip*) and
basic statistics are printed to *stdout*.
2025-05-15 f — added per-file token accounting and statistics.
2025-05-20 f — two-tier extension filtering; stats block no longer copied to
clipboard (terminal only).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import fnmatch
from pathlib import Path
from typing import Iterable, List, Set, Tuple, Dict

import pyperclip

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION ░░░ (editable – do not delete existing rules)
# ─────────────────────────────────────────────────────────────────────────────
PATTERN_IGNORE_FOLDERS: List[str] = [
    ".tmp_dagster_home_",
    "qdrant_storage",
    "backup_",
    "@",
    "cdld_mixed_learning",
]

IGNORE_FOLDERS: List[str] = [
    ".lake", ".github", ".git", ".qodo", ".venv", "qdrant_storage",
    "datasets", "node_modules", ".pnpm-store", ".npm", ".yarn",
    "storybook-static", "typedoc", "docs/.vitepress/dist",
    "cdld_mixed_learning",".devcontainer", ".github", "pytest_cache", "_pycache_", "lib","faiss",
    "EDA","hydraedge.egg-info", 
]

IGNORE_SYSTEM_FOLDERS: List[str] = [
    ".git", "__pycache__", ".astro", ".vscode", ".pnpm", ".vite", ".bin",
    ".cache", "dist", ".next", ".svelte-kit", ".nuxt", ".turbo",
    ".parcel-cache", ".eslintcache", "coverage",
]

# ● lock-files and similar one-offs (skip by exact filename)
IGNORE_FILE_NAMES: List[str] = [
    "pnpm-lock.yaml",
    "package-lock.json",
    "yarn.lock",
    "yarn-error.log",
    "npm-debug.log",
    ".DS_Store",
    "visualize_event_tuples.ipynb",
    "old_rule_approach_rules.ipynb",
]

# ── extension-filtering: two tiers ───────────────────────────────────────────
IGNORE_EXT_FULL: List[str] = [
    ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar",
    ".mat", ".parquet", ".db",
]

IGNORE_EXT_LIST_ONLY: List[str] = [
    ".git", ".dat", ".info", ".log", ".txt", ".json", ".csv", ".geojson",
    ".lock", ".png", ".complete", ".cfg", ".err",
    ".ini", ".out", ".example", ".jpg", ".svg",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".webp", ".avif", ".gif", ".ico",
    ".jsonl", ".tsv", ".py",
]

def _norm(ext: str) -> str:
    return ext if ext.startswith(".") else f".{ext}"

IGNORE_FILE_EXTENSIONS_FULL:  Set[str] = {_norm(e).lower() for e in IGNORE_EXT_FULL}
IGNORE_FILE_EXTENSIONS_LIST: Set[str] = {_norm(e).lower() for e in IGNORE_EXT_LIST_ONLY}

# ● patterns whose *tree node* **and** *file content* are skipped
SKIP_FILE_PATTERNS: List[str] = [
    "package_to_text*.py",
    "*.html",
]

CHARS_PER_TOKEN = 4  # rough heuristic
# ─────────────────────────────────────────────────────────────────────────────

# ╭──────────────────────── helper utils ───────────────────────╮

def approximate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def supports_unicode() -> bool:
    enc = sys.stdout.encoding
    return enc is not None and "UTF" in enc.upper()


def connectors() -> dict[str, str]:
    return {
        "last": "└── " if supports_unicode() else "+-- ",
        "middle": "├── " if supports_unicode() else "|-- ",
        "indent": "│   " if supports_unicode() else "|   ",
        "space": "    ",
    }


def matches_skip_patterns(name: str) -> bool:
    low_name = name.lower()
    return any(fnmatch.fnmatch(low_name, pat.lower()) for pat in SKIP_FILE_PATTERNS)


def has_ignored_ancestor(path: Path | str, names: Iterable[str]) -> bool:
    parts = {p.lower() for p in Path(path).parts}
    return any(ign.lower() in parts for ign in names)


def should_skip_dir(dirname: str) -> bool:
    low = dirname.lower()
    if low in (d.lower() for d in IGNORE_FOLDERS + IGNORE_SYSTEM_FOLDERS):
        return True
    return any(pat.lower() in low for pat in PATTERN_IGNORE_FOLDERS)


def should_skip_file(
    fp: Path, *, exact_names: Iterable[str], context: str
) -> bool:
    if matches_skip_patterns(fp.name):
        return True
    if fp.name in exact_names:
        return True

    ext = fp.suffix.lower()
    if ext in IGNORE_FILE_EXTENSIONS_FULL:
        return True
    if context == "flat" and ext in IGNORE_FILE_EXTENSIONS_LIST:
        return True
    return False

# ╰─────────────────────────────────────────────────────────────╯

def strip_notebook_outputs(path: Path) -> str:
    try:
        with path.open(encoding="utf-8") as f:
            nb = json.load(f)
    except Exception as err:  # noqa: BLE001
        return f"[Could not parse .ipynb as JSON: {err}]"

    for cell in nb.get("cells", []):
        cell.pop("outputs", None)
        cell.pop("attachments", None)
        cell["execution_count"] = None

    return json.dumps(nb, indent=2, ensure_ascii=not supports_unicode())


# ────────────────────────────── ASCII tree ────────────────────────────────

def build_tree(
    path: Path,
    prefix: str = "",
    is_last: bool = True,
    visited: Set[str] | None = None,
) -> List[str]:
    cons = connectors()
    visited = visited or set()
    lines: List[str] = []

    name = path.name
    if matches_skip_patterns(name):
        return lines

    real = str(path.resolve())
    if real in visited:
        return lines
    visited.add(real)

    if has_ignored_ancestor(path, IGNORE_FOLDERS):
        return lines
    if path.is_dir() and should_skip_dir(name):
        return lines

    conn = cons["last" if is_last else "middle"]

    if path.is_dir():
        if name in IGNORE_SYSTEM_FOLDERS:
            lines.append(f"{prefix}{conn}{name}/")
            return lines

        lines.append(f"{prefix}{conn}{name}/")
        children = sorted(path.iterdir(), key=lambda p: p.name.lower())
        for i, child in enumerate(children):
            new_prefix = prefix + (cons["space"] if is_last else cons["indent"])
            lines.extend(
                build_tree(child, new_prefix, i == len(children) - 1, visited)
            )
    else:
        if should_skip_file(path, exact_names=IGNORE_FILE_NAMES, context="tree"):
            return lines
        lines.append(f"{prefix}{conn}{name}")

    return lines


# ─────────────────────────── flat listing ────────────────────────────────

def build_flat_listing(root: Path) -> Tuple[str, Set[str], Dict[str, int]]:
    lines: List[str] = []
    exts: Set[str] = set()
    token_usage: Dict[str, int] = {}

    for cur_dir, dirnames, files in os.walk(root, topdown=True):
        cur_path = Path(cur_dir)
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

        if has_ignored_ancestor(cur_path, IGNORE_FOLDERS):
            continue
        if should_skip_dir(cur_path.name):
            continue

        for fname in sorted(files):
            if matches_skip_patterns(fname):
                continue
            fp = cur_path / fname
            if should_skip_file(fp, exact_names=IGNORE_FILE_NAMES, context="flat"):
                continue

            exts.update({s.lower() for s in (fp.suffixes or [fp.suffix])})

            rel = fp.relative_to(root).as_posix()
            header = f"{rel}\n{'-' * len(rel)}"
            try:
                if fp.suffix.lower() == ".ipynb":
                    content = strip_notebook_outputs(fp)
                else:
                    content = fp.read_text("utf-8")
            except Exception as err:  # noqa: BLE001
                content = f"[Could not read file: {err}]"

            token_count = approximate_tokens(header + "\n" + content + "\n")
            token_usage[rel] = token_count

            lines.extend([header, content, ""])  # trailing blank line

    return "\n".join(lines), exts, token_usage


# ─────────────────────────────────── main ──────────────────────────────────

def main() -> None:  # noqa: C901
    p = argparse.ArgumentParser(description="Dump project tree and file contents to text")
    p.add_argument("--max-tokens", type=int, default=128_000)
    args = p.parse_args()

    root = Path(__file__).resolve().parent
    tree_text = "\n".join(build_tree(root))
    flat_text, ext_set, token_usage = build_flat_listing(root)

    # ── statistics section (terminal only) ─────────────────────────────────
    top3 = sorted(token_usage.items(), key=lambda kv: kv[1], reverse=True)[:3]

    output = (
        "=== PART 1: ASCII TREE ===\n\n" + tree_text +
        "\n\n=== END OF PART 1 ===\n\n" +
        "=== PART 2: FILE CONTENTS ===\n\n" + flat_text +
        "\n=== END OF PART 2 ===\n"
    )

    try:
        pyperclip.copy(output)
        clip_msg = "Combined text copied to clipboard."
    except Exception as e:  # noqa: BLE001
        clip_msg = f"Clipboard copy failed: {e}"

    used = approximate_tokens(output)
    pct = used / args.max_tokens * 100
    print(f"≈ {used:,} tokens of {args.max_tokens:,} ({pct:.2f} %)")
    print(clip_msg)
    if ext_set:
        print("File types included:", ", ".join(sorted(s.lstrip('.') for s in ext_set)))
    print("Top 3 files by token usage:")
    for path, toks in top3:
        print(f"  • {path} — {toks:,} tokens")


if __name__ == "__main__":
    main()