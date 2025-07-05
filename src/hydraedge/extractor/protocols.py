from __future__ import annotations

from typing import List, Dict, Any
import numpy as np
from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str
    filler: str
    alias_key: str
    roles: List[str]
    eid_set: List[str]
    ntype: str
    char_start: int
    char_end: int


class Edge(BaseModel):
    source: str
    target: str
    kind: str


class ExtractionOutput(BaseModel):
    """
    Canonical JSON payload for the tuple extractor (schema v2.4).
    Tests expect both:
      • a `version` field (default "2.4")
      • a `sentence` field
    plus the usual nodes/edges/layouts and a NumPy CHV vector.
    """
    version: str = Field(default="2.4")
    sentence: str
    nodes: List[Node]
    edges: List[Edge]
    layouts: Dict[str, Any]
    chv: np.ndarray

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            np.ndarray: lambda arr: arr.tolist()
        }
