"""
QALIS Dashboard — Metrics Store
================================

Thread-safe in-memory store for real-time QALIS scores.
Designed to be dropped in front of a Prometheus time-series backend
for production deployments.

Paper reference: §3.3 — "Scores were logged to a time-series store
and surfaced via a Grafana dashboard."
"""

import threading
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set


class MetricsStore:
    """
    Thread-safe ring-buffer store for QALIS scores per system.

    Each system maintains a deque of the last ``max_history`` observations.
    Thread safety is provided by a per-system RLock.

    Example::

        store = MetricsStore(max_history=1000)
        store.record("S1", composite=7.4, dimension_scores={"FC": 7.8, ...},
                     violations=[], raw_metrics={})
        latest = store.latest("S1")
    """

    def __init__(self, max_history: int = 10_000) -> None:
        self._max_history = max_history
        self._data: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_history)
        )
        self._lock = threading.RLock()

    def record(
        self,
        system_id: str,
        composite: float,
        dimension_scores: Dict[str, float],
        violations: List[str],
        raw_metrics: Dict[str, Any],
        timestamp: str,
    ) -> None:
        """Append a new observation for *system_id*."""
        entry = {
            "composite":        composite,
            "dimension_scores": dimension_scores,
            "violations":       violations,
            "raw_metrics":      raw_metrics,
            "timestamp":        timestamp,
        }
        with self._lock:
            self._data[system_id].append(entry)

    def latest(self, system_id: str) -> Optional[Dict[str, Any]]:
        """Return the most recent observation for *system_id*, or None."""
        with self._lock:
            buf = self._data.get(system_id)
            if not buf:
                return None
            return dict(buf[-1])

    def history(
        self,
        system_id: str,
        last_n: int = 100,
    ) -> List[Dict[str, Any]]:
        """Return the last *last_n* observations for *system_id* (oldest first)."""
        with self._lock:
            buf = self._data.get(system_id)
            if not buf:
                return []
            items = list(buf)[-last_n:]
            return [dict(e) for e in items]

    def systems(self) -> Set[str]:
        """Return the set of system IDs that have data."""
        with self._lock:
            return set(self._data.keys())

    def clear(self, system_id: Optional[str] = None) -> None:
        """Clear all data for *system_id*, or all systems if None."""
        with self._lock:
            if system_id:
                self._data.pop(system_id, None)
            else:
                self._data.clear()

    def violation_summary(self) -> Dict[str, List[str]]:
        """Return {system_id: [current violations]} for all systems."""
        with self._lock:
            result = {}
            for sid in self._data:
                latest = self.latest(sid)
                if latest:
                    result[sid] = latest.get("violations", [])
            return result
