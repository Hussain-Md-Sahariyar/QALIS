"""
QALIS Structured Logging
========================

Configures structured (JSON-line) logging for production deployments
and plain-text logging for development/analysis scripts.

Usage::

    from qalis.utils.logging import configure_logging, get_logger

    configure_logging(level="INFO", format="json")
    logger = get_logger(__name__)
    logger.info("collector.start", system_id="S1", domain="customer_support")
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line for log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Attach any extra fields set on the record
        for key, val in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName",
                "exc_info", "exc_text",
            }:
                try:
                    json.dumps(val)  # only attach JSON-serialisable extras
                    payload[key] = val
                except TypeError:
                    payload[key] = str(val)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(
    level: str = "INFO",
    fmt: str = "text",  # "text" | "json"
    stream=None,
) -> None:
    """
    Configure root logger for QALIS.

    Args:
        level: Logging level string ("DEBUG", "INFO", "WARNING", "ERROR").
        fmt:   "text" for human-readable output, "json" for structured logs.
        stream: Output stream (default: sys.stdout).
    """
    handler = logging.StreamHandler(stream or sys.stdout)
    if fmt == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-8s %(name)s — %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Suppress noisy third-party loggers
    for noisy in ("transformers", "sentence_transformers", "urllib3", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (convenience wrapper)."""
    return logging.getLogger(name)
