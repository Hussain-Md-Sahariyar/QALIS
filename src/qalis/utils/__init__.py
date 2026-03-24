"""
QALIS Utilities Package
=======================

Shared helper modules used across the framework.

Modules:
    scoring      Metric normalisation and threshold checking (used by collectors)
    io           Data loading/saving helpers (CSV, JSON, JSONL, gzip)
    logging      Structured logging configuration
    validation   Input validation and schema checks
"""

from qalis.utils.scoring import normalise_metrics, check_threshold
from qalis.utils.io import load_csv, load_json, save_json, load_jsonl, save_jsonl
from qalis.utils.validation import validate_config, validate_interaction

__all__ = [
    "normalise_metrics",
    "check_threshold",
    "load_csv",
    "load_json",
    "save_json",
    "load_jsonl",
    "save_jsonl",
    "validate_config",
    "validate_interaction",
]
