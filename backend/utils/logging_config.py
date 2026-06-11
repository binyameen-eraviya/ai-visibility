"""Central logging configuration.

Configures the root logger with a consistent, structured-ish line format and a
level taken from the LOG_LEVEL env var (default INFO). Called once at app
startup (main.py) and at worker startup. Use `logging.getLogger(__name__)` in
modules rather than `print()`.
"""

import logging
import os
import sys

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def configure_logging() -> None:
    """Configure the root logger from LOG_LEVEL (idempotent)."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        stream=sys.stdout,
        force=True,  # override any handlers uvicorn/celery installed first
    )
