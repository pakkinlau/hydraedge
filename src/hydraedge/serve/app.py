# ──────────────────────────────────────────────────────────────
# src/hydraedge/serve/app.py
#
# FastAPI micro-service for the HydraEdge linker.
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import os
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from hydraedge.extractor.tuple_extractor import extract
from hydraedge.encoder import encode_chv
from hydraedge.index.faiss_index import FaissIndex

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.INFO)

# ------------------------------------------------------------------
# Lazy-loaded FAISS index
# ------------------------------------------------------------------
_INDEX: Optional[FaissIndex] = None
_FALLBACK_DIM = 4096
_DEFAULT_PATH = os.getenv("HYDRA_FAISS_INDEX", "tiny.index")


def _ensure_index() -> FaissIndex:
    """
    Return a ready-to-query FaissIndex instance.

    ① Try to load from disk once.
    ② If that fails, create an empty in-memory Flat index so that
       /ping and unit-tests still import without crashing.
    """
    global _INDEX
    if _INDEX is not None:
        return _INDEX

    try:
        _INDEX = FaissIndex.load(_DEFAULT_PATH)
        _LOG.info("Loaded FAISS index «%s» (ntotal=%d)",
                  _DEFAULT_PATH, _INDEX.ntotal)
    except Exception as exc:          # noqa: BLE001 — broad but intentional
        _LOG.warning(
            "⚠️  Could not load FAISS index from «%s»: %s  – "
            "falling back to an empty in-memory index.",
            _DEFAULT_PATH, exc,
        )
        _INDEX = FaissIndex.new(dim=_FALLBACK_DIM, metric="cosine")

    return _INDEX


# ------------------------------------------------------------------
# FastAPI app & models
# ------------------------------------------------------------------
app = FastAPI(title="HydraEdge Linker API", version="0.1.0")


class LinkRequest(BaseModel):
    sentence: str
    top_k: int = 5


class LinkResponse(BaseModel):
    ids: List[str]
    scores: List[float]


# ------------------------------------------------------------------
# Health-check
# ------------------------------------------------------------------
@app.get("/ping")
async def ping():
    """Simple liveness probe used by unit-tests."""
    return {"pong": True}


# ------------------------------------------------------------------
# Main linking endpoint
# ------------------------------------------------------------------
@app.post("/link", response_model=LinkResponse)
async def link(req: LinkRequest):
    """
    1 ▪︎ Tuple-extract from raw sentence  
    2 ▪︎ Encode into a CHV vector  
    3 ▪︎ ANN search over the FAISS index
    """
    try:
        payload, _ = extract(req.sentence)          # (json, chv_vec) tuple
    except Exception as exc:                        # noqa: BLE001
        raise HTTPException(400, f"Extraction failed: {exc}") from exc

    # fallback when extractor returns only nodes
    chv_vec = encode_chv(
        [(n["roles"][0], n["filler"])
         for n in payload["nodes"] if n["roles"][0] != "CHV"]
    )

    index = _ensure_index()
    try:
        ids, scores = index.search(chv_vec, k=req.top_k)
    except Exception as exc:                        # noqa: BLE001
        raise HTTPException(500, f"Index search failed: {exc}") from exc

    return LinkResponse(ids=ids, scores=scores)
