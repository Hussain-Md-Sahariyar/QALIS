"""
QALIS Prometheus Exporter
==========================

Exposes QALIS quality metrics as Prometheus gauges at a configurable
HTTP /metrics endpoint.  Integrates with QALISStreamCollector via the
on_flush callback pattern.

Gauge names match those defined in src/qalis/dashboard/prometheus.py
so that the Grafana dashboard shipped with the repository works without
any relabelling rules.

Gauge registry:
    qalis_composite_score{system_id}           Composite score (0–10)
    qalis_dimension_score{system_id, dimension} Per-dimension score (0–10)
    qalis_metric_value{system_id, metric_id}    Raw per-metric value
    qalis_threshold_violations_total{system_id, metric_id}  Cumulative violations
    qalis_observations_total{system_id}         Total evaluated interactions

Usage::

    from toolkit.exporters.prometheus_exporter import PrometheusExporter
    from toolkit.collectors.qalis_collector import QALISStreamCollector

    exporter = PrometheusExporter(system_id="MY_SYS", port=9090)
    exporter.start()   # starts /metrics HTTP server in background thread

    stream = QALISStreamCollector(system_id="MY_SYS", flush_interval_seconds=300)
    stream.on_flush(exporter.update)   # register as flush callback

    # At shutdown:
    exporter.stop()

Standalone (without streaming)::

    exporter = PrometheusExporter(system_id="MY_SYS", port=9090)
    exporter.start()
    exporter.record(result)   # push a single QALISResult

Paper reference: §4.5 (Toolkit), deployment_guide §5 (Prometheus / Grafana).
"""

from __future__ import annotations

import logging
import threading
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from toolkit.collectors.qalis_collector import QALISResult, QALISBatchResult

logger = logging.getLogger(__name__)


class PrometheusExporter:
    """
    Prometheus metrics exporter for QALIS.

    Requires ``prometheus_client`` (included in requirements.txt).

    Args:
        system_id:   System identifier used as the ``system_id`` label.
        port:        Port for the /metrics HTTP server (default 9090).
        namespace:   Prometheus metric namespace prefix (default "qalis").
    """

    def __init__(
        self,
        system_id: str,
        port: int = 9090,
        namespace: str = "qalis",
    ):
        self.system_id = system_id
        self.port = port
        self.namespace = namespace
        self._server_thread: Optional[threading.Thread] = None
        self._started = False
        self._gauges: dict = {}
        self._counters: dict = {}

        self._init_metrics()

    def _init_metrics(self) -> None:
        """Register Prometheus gauge and counter objects."""
        try:
            from prometheus_client import Gauge, Counter, REGISTRY
            ns = self.namespace

            self._gauges["composite"] = Gauge(
                f"{ns}_composite_score",
                "QALIS composite quality score (0–10)",
                ["system_id"],
            )
            self._gauges["dimension"] = Gauge(
                f"{ns}_dimension_score",
                "QALIS per-dimension quality score (0–10)",
                ["system_id", "dimension"],
            )
            self._gauges["metric_value"] = Gauge(
                f"{ns}_metric_value",
                "Raw QALIS metric value",
                ["system_id", "metric_id"],
            )
            self._counters["violations"] = Counter(
                f"{ns}_threshold_violations_total",
                "Cumulative threshold violations per metric",
                ["system_id", "metric_id"],
            )
            self._counters["observations"] = Counter(
                f"{ns}_observations_total",
                "Total LLM interactions evaluated by QALIS",
                ["system_id"],
            )
            logger.debug("Prometheus metrics registered under namespace '%s'.", ns)
        except ImportError:
            logger.warning(
                "prometheus_client not installed — PrometheusExporter will be "
                "a no-op. Install with: pip install prometheus-client"
            )

    def start(self) -> None:
        """Start the Prometheus /metrics HTTP server in a daemon thread."""
        if self._started:
            return
        try:
            from prometheus_client import start_http_server
            self._server_thread = threading.Thread(
                target=start_http_server,
                args=(self.port,),
                daemon=True,
                name=f"qalis-prometheus-{self.system_id}",
            )
            self._server_thread.start()
            self._started = True
            logger.info(
                "Prometheus /metrics server started on port %d — system=%s",
                self.port, self.system_id,
            )
        except ImportError:
            logger.warning(
                "prometheus_client not installed; /metrics server not started."
            )
        except OSError as exc:
            logger.error("Could not start Prometheus server on port %d: %s",
                         self.port, exc)

    def stop(self) -> None:
        """Signal stop (the daemon thread will exit when the process exits)."""
        self._started = False
        logger.info("PrometheusExporter stop requested — system=%s", self.system_id)

    def record(self, result: "QALISResult") -> None:
        """
        Update Prometheus gauges from a single QALISResult.

        Args:
            result: QALISResult from QALISCollector.evaluate().
        """
        if not self._gauges:
            return
        try:
            sid = self.system_id

            self._gauges["composite"].labels(system_id=sid).set(
                result.composite_score
            )
            for dim, score in result.dimension_scores.items():
                self._gauges["dimension"].labels(
                    system_id=sid, dimension=dim
                ).set(score)

            for mid, val in result.metrics.items():
                if isinstance(val, (int, float)):
                    self._gauges["metric_value"].labels(
                        system_id=sid, metric_id=mid
                    ).set(float(val))

            for mid in result.threshold_violations:
                self._counters["violations"].labels(
                    system_id=sid, metric_id=mid
                ).inc()

            self._counters["observations"].labels(system_id=sid).inc()
        except Exception as exc:
            logger.error("PrometheusExporter.record error: %s", exc)

    def update(self, batch_result: "QALISBatchResult") -> None:
        """
        Update gauges from a QALISBatchResult (on_flush callback).

        Sets composite and dimension gauges to the batch mean values.

        Args:
            batch_result: QALISBatchResult from QALISStreamCollector.flush().
        """
        if not self._gauges or not batch_result.results:
            return
        try:
            summary = batch_result.summary()
            sid = self.system_id

            self._gauges["composite"].labels(system_id=sid).set(
                summary.get("composite_mean", 0)
            )
            for dim, mean in summary.get("dimension_means", {}).items():
                self._gauges["dimension"].labels(
                    system_id=sid, dimension=dim
                ).set(mean)

            # Increment observations and violations counters
            self._counters["observations"].labels(system_id=sid).inc(
                batch_result.n_evaluated
            )
            for result in batch_result.results:
                for mid in result.threshold_violations:
                    self._counters["violations"].labels(
                        system_id=sid, metric_id=mid
                    ).inc()
        except Exception as exc:
            logger.error("PrometheusExporter.update error: %s", exc)

    @property
    def is_running(self) -> bool:
        """True if the /metrics HTTP server is active."""
        return self._started
