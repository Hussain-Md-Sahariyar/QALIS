"""
QALIS Dashboard — Prometheus Metrics Exporter
=============================================

Exports QALIS quality scores as Prometheus metrics for Grafana dashboards.

Metrics exposed (all labelled with ``system_id``):
    qalis_composite_score          Gauge   Composite QALIS score (0–10)
    qalis_dimension_score          Gauge   Per-dimension score (label: dimension)
    qalis_threshold_violations_total  Counter  Running count of violations
    qalis_observations_total       Counter  Running count of evaluations

Paper reference: §3.3 — "Scores were surfaced via a Grafana dashboard
with a 60-second refresh interval."
Configuration: configs/monitoring_config.yaml > dashboard.
"""

import logging
import threading
from typing import Dict, List

logger = logging.getLogger(__name__)

try:
    from prometheus_client import (
        CollectorRegistry, Counter, Gauge,
        generate_latest, CONTENT_TYPE_LATEST,
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    logger.warning(
        "prometheus_client not installed. Install with: pip install prometheus-client\n"
        "PrometheusExporter will emit empty metrics until then."
    )


class PrometheusExporter:
    """
    Maintains Prometheus gauges and counters for all QALIS metrics.

    Thread-safe: ``update()`` may be called from multiple threads.

    Example::

        store = MetricsStore()
        exporter = PrometheusExporter(store)
        # After each collector.collect():
        exporter.update("S1", composite=7.4, dim_scores={...}, violations=[])
        # In Prometheus scrape handler:
        return exporter.render()
    """

    DIMENSIONS = ["functional_correctness", "robustness", "semantic_faithfulness",
                  "safety_security", "transparency", "system_integration"]

    def __init__(self, store=None) -> None:
        self._store = store
        self._lock  = threading.Lock()

        if not _PROMETHEUS_AVAILABLE:
            self._enabled = False
            return

        self._enabled  = True
        self._registry = CollectorRegistry()

        self._composite = Gauge(
            "qalis_composite_score",
            "QALIS composite quality score (0–10)",
            ["system_id"],
            registry=self._registry,
        )
        self._dimension = Gauge(
            "qalis_dimension_score",
            "QALIS per-dimension quality score (0–10)",
            ["system_id", "dimension"],
            registry=self._registry,
        )
        self._violations = Counter(
            "qalis_threshold_violations_total",
            "Cumulative QALIS threshold violations",
            ["system_id", "metric_id"],
            registry=self._registry,
        )
        self._observations = Counter(
            "qalis_observations_total",
            "Total QALIS evaluations performed",
            ["system_id"],
            registry=self._registry,
        )

    def update(
        self,
        system_id: str,
        composite: float,
        dim_scores: Dict[str, float],
        violations: List[str],
    ) -> None:
        """Update gauges/counters for one evaluation result."""
        if not self._enabled:
            return
        with self._lock:
            self._composite.labels(system_id=system_id).set(composite)
            for dim, score in dim_scores.items():
                self._dimension.labels(system_id=system_id, dimension=dim).set(score)
            for metric_id in violations:
                self._violations.labels(system_id=system_id, metric_id=metric_id).inc()
            self._observations.labels(system_id=system_id).inc()

    def render(self) -> str:
        """Return Prometheus text format exposition."""
        if not self._enabled:
            return "# prometheus_client not installed\n"
        return generate_latest(self._registry).decode("utf-8")

    @property
    def content_type(self) -> str:
        if not _PROMETHEUS_AVAILABLE:
            return "text/plain"
        return CONTENT_TYPE_LATEST
