#!/usr/bin/env python3
"""
print_remote_changes.py — PKB synopsis · recent commits · change digest
═══════════════════════════════════════════════════════════════════════
v1.14 (2025-06-26)  Pak Kin Lau · MIT

Changes since v1.13
────────────────────
✓ ENH  Introduced fine-grained file-type allow-list (`SCAN_EXT`) so that only
       human-readable source files are processed; binary artefacts such as
       NumPy `.npy` arrays are now skipped entirely.
✓ ENH  Added `.npy` to `BINARY_EXT`; diffs for these files collapse to the
       placeholder “[binary file]”, preventing clipboard overflows.
✓ No other functional changes; overall flow and CLI flags remain identical.
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set

# ───── Repository root ───────────────────────────────────────────────
def repo_root() -> Path:
    """Absolute path of the repository toplevel."""
    out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"])
    return Path(out.decode("utf-8", "replace").strip()).resolve()


ROOT = repo_root()

# ───── Configuration ────────────────────────────────────────────────
NUM_COMMITS_DEFAULT   = 4
REMOTE_BASE_DEFAULT   = "origin/main"

PATCH_LINE_CAP        = 2_000
EXT_PATCH_CAP         = {".ipynb": 80}
IPYNB_HEAD_TAIL       = 40
TOKEN_SKIP_THRESH     = 3_000
AVG_CHARS             = 40
NEW_PREVIEW_LINES     = 10
CHARS_PER_TOKEN       = 4

BINARY_EXT: Set[str]  = {
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar", ".gz", ".tgz",
    ".rar", ".mp4", ".mov", ".pptx", ".npy"  # ← added .npy
}

# Only files with these extensions will be scanned/rendered
SCAN_EXT: Set[str] = {
    ".py", ".ipynb", ".md", ".txt", ".rst", ".json", ".yaml", ".yml"
}

IGNORE_NAMES: Set[str] = {
    ".git", "Thumbs.db", "__pycache__", ".DS_Store", "@datasets"
}
PATTERN_IGNORE_FOLDERS = ["qdrant_storage", "backup_"]

MAX_TOKENS = 128_000

# ───── Path anchoring helper ─────────────────────────────────────────
def _anchor(path: str) -> str:
    """
    Return a concise, meaningful anchor for a long repository path.

    • If any segment starts with '@' we keep that segment and everything
      after it.
    • Otherwise keep the first **two** segments – enough to orient the
      reviewer.
    """
    parts = path.split("/")
    for i, p in enumerate(parts):
        if p.startswith("@"):
            return "/".join(parts[i:])
    return "/".join(parts[:2]) if len(parts) >= 2 else path


# ───── Human-prompt for LLM commit messages ──────────────────────────
LLM_COMMIT_PROMPT = """\
---
### 📝 Enhanced Commit-Message Task (for ChatGPT / any LLM)

Your reply **must contain three clearly labelled sections**:

1️⃣ **Overall Snapshot** – one concise paragraph (≤ 4 sentences) giving a
   high-level picture of what the *entire* change set achieves.

2️⃣ **Progress vs Recent Commits** – 2-4 bullet points comparing *this*
   change set against the “Recent Commits” list above; highlight concrete
   advances, refactors or reversions.

3️⃣ **Commit List** – the familiar circled-numeral format:

  ① **<Short Title>** – natural-language summary (<file₁>, <file₂>)  
  ② **…**

* Keep the ①/②/③… glyphs.
* At the end of each line list the 1-3 *anchor paths* that best illustrate
  the change.
* ≤ 72 characters per line.
"""

PKB_SYNOPSIS = """\
### PKB in One Glance
Concept → Practice → Tool → Pipeline ↘︎ Programme → Project  
          ↘︎ KPI ↑
* Seven layers give **lineage** from principles → artefacts.  
* YAML `links:` define edges ⇒ *acyclic*, queryable with one `SHORTEST_PATH()`.  
* CI lints schema & reachability; nightly CD reloads Neo4j + Sigma dashboard.
"""

# ───── Utility helpers ───────────────────────────────────────────────
def git(*args: str, _raw: bool = False) -> str | bytes:
    out = subprocess.check_output(["git", "-C", str(ROOT), *args])
    return out if _raw else out.decode("utf-8", "replace")


def approx_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def path_ignored(rel: str) -> bool:
    parts = Path(rel).parts
    if any(p in IGNORE_NAMES for p in parts):
        return True
    return any(pat in seg for pat in PATTERN_IGNORE_FOLDERS for seg in parts)


def ext_allowed(rel: str) -> bool:
    """True iff the path ends with a whitelisted (scan-worthy) extension."""
    return Path(rel).suffix.lower() in SCAN_EXT


def safe_int(tok: str) -> int:
    return int(tok) if tok.isdigit() else 0


def chunked(seq: List[str], limit: int):
    buf, size = [], 0
    for s in seq:
        inc = len(s) + 1
        if size + inc > limit and buf:
            yield buf
            buf, size = [], 0
        buf.append(s)
        size += inc
    if buf:
        yield buf


# ───── Commit list helpers ───────────────────────────────────────────
def fetch_commits(n: int) -> List[dict]:
    fmt = "%H%x00%h%x00%an%x00%ad%x00%s%x01"
    raw = git("log", f"-n{n}", "--date=iso-strict", f"--pretty=format:{fmt}")
    out: List[dict] = []
    for blk in raw.split("\x01"):
        if blk.strip():
            _, short, auth, date, subj = blk.split("\x00")
            out.append(
                {"short": short, "author": auth, "date": date, "subject": subj}
            )
    return out


def render_commits(lst: List[dict]) -> str:
    return "\n".join(
        f"{c['author']} – {c['date']} ({c['short']}):\n- {c['subject']}\n"
        for c in lst
    ).rstrip()


# ───── Diff / patch helpers ──────────────────────────────────────────
def plusminus_only(diff: str) -> List[str]:
    return [
        ln
        for ln in diff.splitlines()
        if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))
    ]


def head_tail(lines: List[str], keep: int) -> List[str]:
    if len(lines) <= keep * 2:
        return lines
    return lines[:keep] + ["…"] + lines[-keep:]


def _filter_ipynb_payload(lines: List[str]) -> List[str]:
    """Remove attachment / image-blob lines from a .ipynb diff."""
    return [
        ln
        for ln in lines
        if '"image/png"' not in ln and '"attachments"' not in ln
    ]


def full_patch(rel: str, base: str | None, plusminus: bool) -> str:
    ext = Path(rel).suffix.lower()
    cap = EXT_PATCH_CAP.get(ext, PATCH_LINE_CAP)
    args = (
        ["diff", "-U0", "--", rel]
        if base is None
        else ["diff", f"{base}...HEAD", "-U0", "--", rel]
    )
    try:
        diff = git(*args)
    except subprocess.CalledProcessError:
        return "[diff error]"

    lines = plusminus_only(diff) if plusminus else diff.splitlines()

    if ext == ".ipynb":
        lines = _filter_ipynb_payload(lines)
        lines = head_tail(lines, IPYNB_HEAD_TAIL)

    if cap and len(lines) > cap:
        lines = lines[:cap] + [f"[truncated {len(lines) - cap} lines]"]

    return "\n".join(lines)


def file_head(fp: Path, n: int) -> str:
    try:
        with fp.open("r", encoding="utf-8", errors="replace") as f:
            return "".join(next(f) for _ in range(n)).rstrip("\n")
    except Exception:
        return "[empty file]"


def numstat(paths: List[str], base: str | None) -> Dict[str, Tuple[int, int]]:
    stats: Dict[str, Tuple[int, int]] = {}
    cmd = ["diff", "--numstat", "-z"]
    if base:
        cmd.insert(1, f"{base}...HEAD")
    for batch in chunked(paths, 8000):
        raw = git(*cmd, "--", *batch, _raw=True)
        for rec in raw.split(b"\0"):
            if rec:
                a, d, p = rec.decode("utf-8", "replace").split("\t")[:3]
                stats[p] = (safe_int(a), safe_int(d))
        print("∑", end="", flush=True)
    return stats


# ───── File collectors (robust) ──────────────────────────────────────
def _parse_name_status_z(data: bytes) -> List[Tuple[str, str]]:
    """Parse `git diff --name-status -z` output."""
    out: List[Tuple[str, str]] = []
    tok = data.split(b"\0")
    i = 0
    while i < len(tok):
        if not tok[i]:
            i += 1
            continue
        code = tok[i].decode()
        if code[0] in "RC":  # rename / copy
            src = tok[i + 1].decode("utf-8", "replace")
            dest = tok[i + 2].decode("utf-8", "replace")
            out.append(("D", src))
            out.append(("A", dest))
            i += 3
        else:  # ordinary record
            path = tok[i + 1].decode("utf-8", "replace")
            out.append((code[0], path))
            i += 2
    return out


def collect_local() -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []

    # Tracked modifications / deletions / renames
    diff_raw = git("diff", "--name-status", "-z", _raw=True)
    rows.extend(_parse_name_status_z(diff_raw))

    # Staged-but-uncommitted changes
    diff_cached = git("diff", "--cached", "--name-status", "-z", _raw=True)
    rows.extend(_parse_name_status_z(diff_cached))

    # Untracked files
    untracked = git(
        "ls-files", "--others", "--exclude-standard", "-z", _raw=True
    )
    for f in untracked.split(b"\0"):
        if f:
            rows.append(("??", f.decode("utf-8", "replace")))

    # Deduplicate while preserving order
    seen: Set[str] = set()
    uniq: List[Tuple[str, str]] = []
    for st, rel in rows:
        if (
            rel not in seen
            and not path_ignored(rel)
            and ext_allowed(rel)
            and not (ROOT / rel).is_dir()
        ):
            uniq.append((st, rel))
            seen.add(rel)
    return uniq


def collect_remote(base: str) -> List[Tuple[str, str]]:
    diff_raw = git("diff", "--name-status", "-z", f"{base}...HEAD", _raw=True)
    rows = _parse_name_status_z(diff_raw)

    seen: Set[str] = set()
    uniq: List[Tuple[str, str]] = []
    for st, rel in rows:
        if (
            rel not in seen
            and not path_ignored(rel)
            and ext_allowed(rel)
        ):
            uniq.append((st, rel))
            seen.add(rel)
    return uniq


# ───── Report generation ────────────────────────────────────────────
def render_report(
    rows: List[Tuple[str, str]],
    base: str | None,
    plusminus_cmd: bool,
) -> Tuple[str, int, int]:
    tbl = ["| Path | Δ+ | Δ- | St |", "|---|---:|---:|:--:|"]
    blocks: List[str] = []
    tok_total = 0
    stats = numstat([r for _, r in rows], base)
    print()

    for st, rel in rows:
        ins, dele = stats.get(rel, (0, 0))
        fp = ROOT / rel
        ext = fp.suffix.lower()
        plusminus = plusminus_cmd or ext == ".ipynb"
        rel_anchor = _anchor(rel)

        if st == "D":
            pv = (
                "[deleted binary file]"
                if ext in BINARY_EXT
                else full_patch(rel, base, plusminus)
            )
        elif st in ("A", "??"):
            pv = (
                "[new binary file]"
                if ext in BINARY_EXT
                else file_head(fp, NEW_PREVIEW_LINES)
            )
        elif ext in BINARY_EXT:
            pv = "[binary file]"
        else:
            est = (ins + dele) * AVG_CHARS // CHARS_PER_TOKEN
            pv = (
                "[diff skipped]"
                if est > TOKEN_SKIP_THRESH
                else full_patch(rel, base, plusminus)
            )

        tok_total += approx_tokens(pv)
        tbl.append(f"`{rel_anchor}` | {ins} | {dele} | {st} |")
        fence = "diff" if pv.startswith("diff") else "text"
        blocks.append(f"\n#### {rel_anchor}\n\n```{fence}\n{pv}\n```\n")
        print("δ", end="", flush=True)

    full = "### Commit Report\n" + "\n".join(tbl) + "".join(blocks)
    return full, tok_total, len(tbl) - 1


# ───── Clipboard helper ──────────────────────────────────────────────
def copy_clip(text: str):
    try:
        import pyperclip

        pyperclip.copy(text)
    except Exception:
        sys_platform = platform.system()
        if sys_platform == "Windows":
            subprocess.run(["clip"], input=text, text=True, check=False)
        elif sys_platform == "Darwin":
            subprocess.run(["pbcopy"], input=text, text=True, check=False)
        else:
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text,
                text=True,
                check=False,
            )


# ───── Main entry-point ─────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("local", "remote"), default="local")
    ap.add_argument("-b", "--base", default=REMOTE_BASE_DEFAULT)
    ap.add_argument("-n", "--num", type=int, default=NUM_COMMITS_DEFAULT)
    ap.add_argument("--plusminus", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--no-clip", action="store_true")
    cfg = ap.parse_args()

    if cfg.mode == "remote":
        try:
            git("fetch", "--prune")
        except Exception:
            pass

    parts = [
        PKB_SYNOPSIS,
        "\n---\n",
        f"### Recent Commits (last {cfg.num})\n",
        render_commits(fetch_commits(cfg.num)),
        "\n---\n",
    ]

    rows = (
        collect_remote(cfg.base) if cfg.mode == "remote" else collect_local()
    )
    print("σ", end="", flush=True)
    report, toks, nfiles = render_report(
        rows,
        cfg.base if cfg.mode == "remote" else None,
        cfg.plusminus,
    )
    parts.append(report)
    parts.append(LLM_COMMIT_PROMPT)

    md = "\n".join(parts).rstrip()
    md += f"\n\nFiles: {nfiles} | Tokens: {toks}/{MAX_TOKENS}\n"

    if not cfg.no_clip:
        copy_clip(md)

    print(md if cfg.show else f"Files: {nfiles} | Tokens: {toks}/{MAX_TOKENS}")


if __name__ == "__main__":
    main()
