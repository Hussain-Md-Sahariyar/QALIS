"""
LogCollector — Offline QALIS metric collection from stored request logs.

Replays interactions from the raw request log CSVs produced by each case
system (data/raw/{system}/request_logs/) and produces QALISResult objects
identical to those generated in real time during the study.

Paper reference: §3.3 — "Logs were replayed offline to compute metrics
that require additional context not available at inference time."
"""

import csv
import gzip
import json
import logging
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from qalis.collectors.collector import CollectorConfig, QALISCollector
from qalis.result import QALISResult

logger = logging.getLogger(__name__)


class LogCollector:
    """
    Replay stored request logs to produce QALISResult objects.

    Supports CSV and gzipped CSV formats produced by the case systems.
    Columns expected: ``query``, ``response``, and optionally ``context``,
    ``latency_ms``, ``reference_answer``, ``request_id``.

    Example::

        lc = LogCollector(
            CollectorConfig(system_id="S1", domain="customer_support"),
            log_path="data/raw/S1_Customer_Support_Chatbot/request_logs/",
        )
        for result in lc.replay(max_rows=500):
            store(result)
    """

    def __init__(self, config: CollectorConfig, log_path: str) -> None:
        self.config = config
        self.log_path = Path(log_path)
        self._collector = QALISCollector(config)

    def replay(
        self,
        max_rows: Optional[int] = None,
        skip_errors: bool = True,
    ) -> Generator[QALISResult, None, None]:
        """
        Yield QALISResult objects by replaying log rows one by one.

        Args:
            max_rows:    Stop after this many rows (None = all rows).
            skip_errors: If True, log and skip rows that raise exceptions.

        Yields:
            QALISResult for each successfully replayed interaction.
        """
        log_files = sorted(self.log_path.glob("*.csv")) + \
                    sorted(self.log_path.glob("*.csv.gz"))
        if not log_files:
            raise FileNotFoundError(f"No CSV logs found at {self.log_path}")

        count = 0
        for log_file in log_files:
            opener = gzip.open if log_file.suffix == ".gz" else open
            with opener(log_file, "rt", newline="") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    if max_rows is not None and count >= max_rows:
                        return
                    try:
                        result = self._replay_row(row)
                        count += 1
                        yield result
                    except Exception as exc:
                        if skip_errors:
                            logger.warning("LogCollector: skipping row %d: %s", count, exc)
                        else:
                            raise

    def _replay_row(self, row: Dict[str, str]) -> QALISResult:
        """Convert a single CSV row to a QALISResult."""
        context_raw = row.get("context", "")
        context: List[str] = []
        if context_raw:
            try:
                context = json.loads(context_raw)
            except (json.JSONDecodeError, TypeError):
                context = [context_raw]

        latency = row.get("latency_ms") or row.get("response_time_ms")
        latency_ms = float(latency) if latency else None

        return self._collector.collect(
            query=row.get("query", row.get("prompt", "")),
            response=row.get("response", row.get("completion", "")),
            context=context,
            reference_answer=row.get("reference_answer") or None,
            latency_ms=latency_ms,
            api_error=row.get("api_error", "false").lower() == "true",
            request_id=row.get("request_id") or row.get("query_id") or None,
        )

    def replay_all(self, **kwargs) -> List[QALISResult]:
        """Convenience wrapper: collect all results into a list."""
        return list(self.replay(**kwargs))
