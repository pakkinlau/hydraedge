# ────────────────────────────────────────────────────────────────
# wp4_srl_gpu.py
# ----------------------------------------------------------------
# GPU-accelerated SRL backend for HyDRA-Edge
#
# • Exposes a *single* public factory:
#       get_gpu_srl_model(device: str = "cuda:0",
#                          model_name: str | None = None)
#
# • Returns a Hugging-Face `pipeline` object ready for inference.
#   The caller (generic SRL stage) handles sentence pre-/post-
#   processing, verb marking, batching, etc.
#
# • Model checkpoint
#       default = "dannashao/bert-base-uncased-finetuned-srl_arg"
#   This checkpoint follows the SRL-ARG convention and expects a
#   “[V] ” token inserted immediately before the target predicate.
#
# • Automatic fallback: if CUDA not available, the factory will
#   raise RuntimeError — the caller should catch and fall back to
#   a CPU-only SRL implementation.
#
# Dependencies: transformers ≥4.41, torch ≥2.3
# ----------------------------------------------------------------
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Protocol

import torch
from transformers import AutoTokenizer, pipeline

logger = logging.getLogger(__name__)
_DEFAULT_MODEL = "dannashao/bert-base-uncased-finetuned-srl_arg"


class SrlPipelineProtocol(Protocol):
    """Subset of HF pipeline interface used downstream."""

    def __call__(self, sentence: str):  # noqa: D401, ANN001
        ...

    # `pipeline` objects are callable; no additional methods required.


# ╭──────────────────────────────────────────────────────────────╮
# │ Factory (cached)                                             │
# ╰──────────────────────────────────────────────────────────────╯
@lru_cache(maxsize=2)
def get_gpu_srl_model(
    device: str = "cuda:0",
    model_name: str | None = None,
) -> SrlPipelineProtocol:
    """Return a singleton GPU SRL pipeline.

    Parameters
    ----------
    device :
        Torch device string.  Must be a valid CUDA device such as
        "cuda" or "cuda:0".  Passing "cpu" will raise RuntimeError.
    model_name :
        Hugging-Face checkpoint name.  If *None*, uses the default
        PropBank-fine-tuned BERT model.

    Raises
    ------
    RuntimeError
        If CUDA is unavailable or the requested device is not CUDA.
    """
    if device.startswith("cpu"):
        raise RuntimeError("GPU SRL requested with CPU device.")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA device not available for GPU SRL.")

    mdl = model_name or _DEFAULT_MODEL
    logger.info("Loading GPU SRL pipeline %s on %s …", mdl, device)

    tok = AutoTokenizer.from_pretrained(mdl)
    srl_pipe: SrlPipelineProtocol = pipeline(
        task="token-classification",
        model=mdl,
        tokenizer=tok,
        aggregation_strategy="simple",
        device=device,
    )
    logger.info("GPU SRL pipeline ready (model=%s, device=%s)", mdl, device)
    return srl_pipe
