from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Type

@dataclass
class Ctx:
    text: str
    debug: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)  # artefacts by key

class PipelineStage:
    name: str = "base"
    requires: List[str] = []
    provides: List[str] = []

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config

    def run(self, ctx: Ctx) -> None:
        raise NotImplementedError

# ── automatic registry ────────────────────────────────────────────────
_REGISTRY: Dict[str, Type[PipelineStage]] = {}

def register(cls: Type[PipelineStage]) -> Type[PipelineStage]:
    _REGISTRY[cls.name] = cls
    return cls

def get_stage(name: str) -> Type[PipelineStage]:
    return _REGISTRY[name]