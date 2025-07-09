import logging, sys
from structlog import wrap_logger

_logging = logging.getLogger("linker")
_logging.setLevel(logging.INFO)
_logging.addHandler(logging.StreamHandler(sys.stdout))
logger = wrap_logger(_logging)
__all__ = ["logger"]