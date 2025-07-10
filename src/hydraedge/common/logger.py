#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common/logger.py
────────────────
Thin wrapper around structlog *plus* a timing helper usable as:

    with time_stage("wp2_tokenise"):
        doc = nlp(sentence)

The timing (milliseconds) is emitted at INFO level.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Iterator

# ----------------------------------------------------------------------
# Logger initialisation – robust to missing structlog
# ----------------------------------------------------------------------
try:
    import structlog

    _processor_chain = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=_processor_chain,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    log = structlog.get_logger("hydraedge")

except ModuleNotFoundError:  # fall back to stdlib logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    log = logging.getLogger("hydraedge")
    log.warning("structlog missing – falling back to stdlib logger")

# ----------------------------------------------------------------------
# Timing helper
# ----------------------------------------------------------------------
@contextmanager
def time_stage(stage_name: str) -> Iterator[None]:
    """
    Context-manager that measures wall-clock duration of the enclosed block
    and logs it at INFO level (key: stage_timing).

    Example
    -------
    >>> with time_stage("wp2_tokenise"):
    ...     run_heavy_function()
    """
    t0 = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - t0) * 1_000
    log.info("stage_timing", stage=stage_name, ms=round(elapsed_ms, 3))
