#!/usr/bin/env python3
# print_dir_structure.py  —  drop-in, CLI-free variant
#
# Prints a tree-like view of the current working directory, honouring the
# ignore lists below, copies the result to the clipboard (if pyperclip is
# installed), and shows an approximate OpenAI-token count.
#
# Edit the CONFIGURATION section only; the rest is self-contained.

from __future__ import annotations
import os
from pathlib import Path
from typing import List

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
    ".pytest_cache",             # ignore entire pytest cache
    "datasets", "node_modules", ".pnpm-store", ".npm", ".yarn",
    "storybook-static", "typedoc", "docs/.vitepress/dist",
    "cdld_mixed_learning",
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
]

# ── extension-filtering: two tiers ───────────────────────────────────────────
IGNORE_EXT_FULL: List[str] = [
    ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar",
    ".mat", ".parquet", ".db",
]

IGNORE_EXT_LIST_ONLY: List[str] = [
    ".git", ".dat", ".info", ".log", ".txt", ".json", ".csv", ".geojson",
    ".lock", ".png", ".complete", ".cfg", ".err", ".ini", ".out", ".example",
    ".jpg", ".svg", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".webp",
    ".avif", ".gif", ".ico", ".jsonl", ".tsv", ".py",
]

# ── force-show at root level ────────────────────────────────────────────────
ALWAYS_SHOW_FILES: List[str] = [
    "README.md",
    "pyproject.toml",
]

# ─────────────────────────────────────────────────────────────────────────────
# RUNTIME CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
ROOT_DIR          = Path.cwd()          # starting point
SHOW_ALL_FILES    = False               # True → list *every* file
DEFAULT_EXTENSION = ".ipynb"            # shown when SHOW_ALL_FILES = False
INDENT            = "    "

CHARS_PER_TOKEN   = 4.0                 # heuristic
MAX_TOKENS        = 128_000

try:
    import pyperclip
    _HAS_CLIPBOARD = True
except Exception:
    _HAS_CLIPBOARD = False

# ─────────────────────────────────────────────────────────────────────────────
# CORE LOGIC
# ─────────────────────────────────────────────────────────────────────────────
def scan_dir(
    directory: Path,
    level: int = 0,
    output: list[str] | None = None
) -> list[str]:
    """Recursively collect directory entries, respecting ignore rules."""
    if output is None:
        output = []

    try:
        entries = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return output

    for entry in entries:
        name = entry.name

        # always-show files—but only at the top level
        if level == 0 and entry.is_file() and name in ALWAYS_SHOW_FILES:
            output.append(f"{INDENT*level}|-- {name}")
            continue

        # name-based ignores
        if entry.is_file() and name in IGNORE_FILE_NAMES:
            continue

        if entry.is_dir():
            if (
                name in IGNORE_FOLDERS
                or name in IGNORE_SYSTEM_FOLDERS
                or any(pat in name for pat in PATTERN_IGNORE_FOLDERS)
            ):
                continue
            output.append(f"{INDENT*level}|-- {name}")
            scan_dir(entry, level + 1, output)
        else:
            ext = entry.suffix.lower()

            # extension-based ignores
            if ext in IGNORE_EXT_FULL:
                continue
            if not SHOW_ALL_FILES and ext in IGNORE_EXT_LIST_ONLY:
                continue
            if not SHOW_ALL_FILES and not name.endswith(DEFAULT_EXTENSION):
                continue

            output.append(f"{INDENT*level}|-- {name}")

    return output

def approximate_tokens(text: str) -> int:
    """Coarse GPT-token estimate."""
    return int(len(text) / CHARS_PER_TOKEN + 0.5)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    header     = f"Knowledge Base Directory structure of: {ROOT_DIR}"
    tree_lines = scan_dir(ROOT_DIR)
    output     = "\n".join([header, *tree_lines])

    print(output, end="\n\n")

    if _HAS_CLIPBOARD:
        try:
            pyperclip.copy(output)
            print("[clipboard] copied ✓")
        except pyperclip.PyperclipException:
            print("[clipboard] unavailable ✗")

    tokens = approximate_tokens(output)
    pct    = 100 * tokens / MAX_TOKENS
    print(f"[usage] ~{tokens:,}/{MAX_TOKENS:,} tokens ({pct:.2f} %)")

if __name__ == "__main__":
    main()
