"""
QALIS I/O Utilities
===================

Thin wrappers around CSV, JSON, JSONL, and gzip file I/O used throughout
the framework and analysis scripts.
"""

import csv
import gzip
import json
import logging
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def load_csv(path: PathLike, **pandas_kwargs) -> pd.DataFrame:
    """
    Load a CSV (plain or gzipped) into a DataFrame.

    Auto-detects gzip by ``.gz`` suffix.
    """
    path = Path(path)
    compression = "gzip" if path.suffix == ".gz" else "infer"
    return pd.read_csv(path, compression=compression, **pandas_kwargs)


def save_csv(df: pd.DataFrame, path: PathLike, **pandas_kwargs) -> None:
    """Save a DataFrame to CSV (gzipped if path ends with .gz)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    compression = "gzip" if path.suffix == ".gz" else None
    df.to_csv(path, index=False, compression=compression, **pandas_kwargs)
    logger.debug("Saved CSV → %s (%d rows)", path, len(df))


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def load_json(path: PathLike) -> Any:
    """Load a JSON file (plain or gzipped)."""
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(obj: Any, path: PathLike, indent: int = 2) -> None:
    """Serialise *obj* to a JSON file, creating parent directories as needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "wt", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=indent, ensure_ascii=False)
    logger.debug("Saved JSON → %s", path)


# ---------------------------------------------------------------------------
# JSONL (newline-delimited JSON)
# ---------------------------------------------------------------------------

def load_jsonl(path: PathLike) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dicts."""
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    records: List[Dict[str, Any]] = []
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def save_jsonl(records: List[Any], path: PathLike) -> None:
    """Save a list of dicts/objects as JSONL."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "wt", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.debug("Saved JSONL → %s (%d records)", path, len(records))


def iter_jsonl(path: PathLike) -> Generator[Dict[str, Any], None, None]:
    """Lazily iterate over a JSONL file without loading all records into memory."""
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

def ensure_dir(path: PathLike) -> Path:
    """Create *path* and all parents; return Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
