from __future__ import annotations

import json
import logging
import os
from typing import Any

LEVEL_RANK = {
    "error": logging.ERROR,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}

VERBOSITY_RANK = {
    "error": 0,
    "warn": 1,
    "info": 2,
    "debug": 3,
}


def resolve_log_level() -> str:
    raw = os.getenv("LOG_LEVEL", "warn").strip().lower()
    if raw == "warning":
        raw = "warn"
    return raw if raw in LEVEL_RANK else "warn"


def configure_logging(logger_name: str = "sharingbridge") -> logging.Logger:
    level_name = resolve_log_level()
    logging.basicConfig(
        level=LEVEL_RANK[level_name],
        format="%(message)s",
        force=True,
    )
    return logging.getLogger(logger_name)


def should_log_info() -> bool:
    level = resolve_log_level()
    return VERBOSITY_RANK[level] >= VERBOSITY_RANK["info"]


def log_startup_from_issues(
    logger: logging.Logger,
    config: dict[str, Any],
    issues: list[str],
) -> None:
    if issues:
        logger.warning("[startup] config issues: %s", json.dumps(issues))
    elif should_log_info():
        logger.info("[startup] config %s", json.dumps(config))
