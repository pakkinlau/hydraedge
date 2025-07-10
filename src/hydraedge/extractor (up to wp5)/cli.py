"""
hydraedge.extractor.cli
———————————————
Command-line entry-point for the HyDRA-Edge extractor pipeline.

Usage
-----
$ python -m hydraedge.extractor.cli \
    "Google acquired YouTube for $1.65 billion in 2006." \
    --config config/extractor.yaml \
    --debug

Outputs the validated JSON payload (default) or, with --debug,
a verbose trace of every intermediate stage.

The module is intentionally minimal: it delegates all heavy lifting
to `PipelineRunner`, which in turn relies on automatically registered
`PipelineStage` subclasses (see each wp*.py).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import yaml

from hydraedge.extractor.pipeline import PipelineRunner

def extract_sentence(sentence: str,
                     config_path: str = "config/extractor.yaml",
                     *,
                     debug: bool = False) -> Dict[str, Any]:
    """Return final payload (or full ctx.debug if debug=True)."""
    cfg = _load_config(config_path)
    runner = PipelineRunner(cfg)
    ctx = runner.run_sentence(sentence)
    return ctx.debug if debug else ctx.data["payload"]


def extract_sentence_debug(sentence: str,
                           config_path: str = "config/extractor.yaml") -> Dict[str, Any]:
    """Shorthand for extract_sentence(..., debug=True)."""
    return extract_sentence(sentence, config_path, debug=True)


def extract_doc(doc: str, **kw) -> Dict[str, Any]:          # simple stub
    """Split *doc* into sentences and return list of payloads."""
    import spacy
    nlp = spacy.blank("en")
    return [extract_sentence(sent.text, **kw) for sent in nlp(doc).sents]


def _load_config(path: str | Path) -> Dict[str, Any]:
    """Read YAML config from *path* and return dict.

    If *path* does not exist, raises FileNotFoundError.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def _build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="hydra-extract",
        description="HyDRA-Edge sentence-level tuple extractor",
    )
    ap.add_argument(
        "sentence",
        type=str,
        help="Sentence to extract tuples from.",
    )
    ap.add_argument(
        "--config",
        type=str,
        default="config/extractor.yaml",
        help="Path to extractor YAML config (default: %(default)s).",
    )
    ap.add_argument(
        "--debug",
        action="store_true",
        help="Print full debug trace instead of final payload.",
    )
    ap.add_argument(
        "--indent",
        type=int,
        default=2,
        metavar="N",
        help="Pretty-print JSON with indent N (default: %(default)s).",
    )
    return ap


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    config = _load_config(args.config)
    runner = PipelineRunner(config)

    ctx = runner.run_sentence(args.sentence)

    obj = ctx.debug if args.debug else ctx.data.get("payload", {})
    print(json.dumps(obj, ensure_ascii=False, indent=args.indent))


if __name__ == "__main__":
    main()
