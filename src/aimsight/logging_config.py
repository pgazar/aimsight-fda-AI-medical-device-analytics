"""Console-only structured logging.

Docker, GitHub Actions, and Azure Container Apps Jobs all capture standard
output automatically, so logging to the console is enough for this
project — no committed .log files, no third-party logging library.
Later, pipeline execution results are also recorded in PostgreSQL
operational tables (pipeline_run, api_request_log); this module is only
for human-readable diagnostic output, not durable history.

Levels used in this project:
    DEBUG    detailed local troubleshooting
    INFO     normal pipeline progress
    WARNING  recoverable data-quality issues
    ERROR    failed operations
    CRITICAL failures that must stop publication
"""

import logging
import sys

_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    """Attach one console handler to the root logger, exactly once.

    Safe to call multiple times (e.g. once per module, or repeatedly across
    test files) — later calls are no-ops so we never end up with duplicate
    handlers printing every message twice.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger, configuring logging on first use.

    Usage in any module:
        from aimsight.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("extraction started")
    """
    configure_logging()
    return logging.getLogger(name)
