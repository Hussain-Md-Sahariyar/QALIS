"""
QALIS MLflow Exporter
======================

Logs QALIS metric values, dimension scores, composite scores, and threshold
violations to an MLflow experiment.  Supports both per-interaction logging
(record) and batch flush logging (update).

Each evaluated interaction becomes one MLflow run step, allowing time-series
quality plots in the MLflow UI.  Threshold violations are logged as tags
on the MLflow run for easy filtering.

Usage::

    from toolkit.exporters.mlflow_exporter import MLflowExporter
    from toolkit.collectors.qalis_collector import QALISStreamCollector

    exporter = MLflowExporter(
        system_id="MY_SYS",
        experiment_name="QALIS/MY_SYS",
        tracking_uri="http://mlflow.internal:5000",  # or None for local
    )

    stream = QALISStreamCollector(system_id="MY_SYS", flush_interval_seconds=300)
    stream.on_flush(exporter.update)

Standalone (log a single result)::

    exporter = MLflowExporter(system_id="MY_SYS")
    exporter.start_run()
    exporter.record(result)
    exporter.end_run()

Paper reference: §4.5 (Toolkit), deployment_guide §5 (Monitoring Integration).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from toolkit.collectors.qalis_collector import QALISResult, QALISBatchResult

logger = logging.getLogger(__name__)


class MLflowExporter:
    """
    MLflow experiment logger for QALIS quality metrics.

    Requires ``mlflow`` (included in requirements.txt).

    Args:
        system_id:        System identifier; used as the ``system_id`` tag.
        experiment_name:  MLflow experiment name (created if absent).
        tracking_uri:     MLflow tracking server URI.  None = local ./mlruns.
        run_name:         MLflow run name (default: "qalis-{system_id}").
        log_artifacts:    If True, also log batch CSV results as MLflow artifacts.
    """

    def __init__(
        self,
        system_id: str,
        experiment_name: Optional[str] = None,
        tracking_uri: Optional[str] = None,
        run_name: Optional[str] = None,
        log_artifacts: bool = False,
    ):
        self.system_id        = system_id
        self.experiment_name  = experiment_name or f"QALIS/{system_id}"
        self.tracking_uri     = tracking_uri
        self.run_name         = run_name or f"qalis-{system_id}"
        self.log_artifacts    = log_artifacts
        self._active_run      = None
        self._step: int       = 0
        self._mlflow_available = False

        self._init_mlflow()

    def _init_mlflow(self) -> None:
        try:
            import mlflow
            if self.tracking_uri:
                mlflow.set_tracking_uri(self.tracking_uri)
            mlflow.set_experiment(self.experiment_name)
            self._mlflow_available = True
            logger.debug("MLflow exporter initialised — experiment=%s",
                         self.experiment_name)
        except ImportError:
            logger.warning(
                "mlflow not installed — MLflowExporter will be a no-op. "
                "Install with: pip install mlflow"
            )

    def start_run(self, run_name: Optional[str] = None) -> None:
        """Start a new MLflow run (call once per evaluation session)."""
        if not self._mlflow_available:
            return
        try:
            import mlflow
            self._active_run = mlflow.start_run(
                run_name=run_name or self.run_name
            )
            mlflow.set_tag("system_id", self.system_id)
            mlflow.set_tag("framework", "QALIS")
            logger.info("MLflow run started — experiment=%s run=%s",
                        self.experiment_name, self._active_run.info.run_id)
        except Exception as exc:
            logger.error("MLflowExporter.start_run error: %s", exc)

    def end_run(self) -> None:
        """End the active MLflow run."""
        if not self._mlflow_available:
            return
        try:
            import mlflow
            mlflow.end_run()
            self._active_run = None
            logger.debug("MLflow run ended.")
        except Exception as exc:
            logger.error("MLflowExporter.end_run error: %s", exc)

    def record(self, result: "QALISResult") -> None:
        """
        Log a single QALISResult as one MLflow step.

        Logs:
            - qalis.composite_score
            - qalis.fc, qalis.ro, qalis.sf, qalis.ss, qalis.ti, qalis.iq
            - qalis.{metric_id} for all raw metric values
            - Tag: qalis.violations (comma-separated list, if any)

        Args:
            result: QALISResult from QALISCollector.evaluate().
        """
        if not self._mlflow_available:
            return
        try:
            import mlflow
            metrics: Dict[str, float] = {
                "qalis.composite_score": result.composite_score,
            }
            for dim, score in result.dimension_scores.items():
                metrics[f"qalis.{dim.lower()}"] = score
            for mid, val in result.metrics.items():
                if isinstance(val, (int, float)):
                    metrics[f"qalis.{mid.lower().replace('-', '_')}"] = float(val)

            mlflow.log_metrics(metrics, step=self._step)

            if result.threshold_violations:
                mlflow.set_tag(
                    "qalis.violations",
                    ",".join(result.threshold_violations),
                )

            self._step += 1
        except Exception as exc:
            logger.error("MLflowExporter.record error: %s", exc)

    def update(self, batch_result: "QALISBatchResult") -> None:
        """
        Log batch summary statistics as one MLflow step.

        Called automatically by QALISStreamCollector on_flush.

        Logs:
            - qalis.composite_mean, composite_min, composite_max
            - qalis.{dim}_mean for all dimensions
            - qalis.violation_rate
            - qalis.pass_rate

        Optionally saves the full batch DataFrame as an MLflow artifact
        (when log_artifacts=True).

        Args:
            batch_result: QALISBatchResult from QALISStreamCollector.flush().
        """
        if not self._mlflow_available or not batch_result.results:
            return
        try:
            import mlflow
            summary = batch_result.summary()
            metrics: Dict[str, float] = {
                "qalis.composite_mean":  summary.get("composite_mean", 0),
                "qalis.composite_min":   summary.get("composite_min", 0),
                "qalis.composite_max":   summary.get("composite_max", 0),
                "qalis.violation_rate":  summary.get("violation_rate", 0),
                "qalis.pass_rate":       summary.get("pass_rate", 0),
                "qalis.n_evaluated":     float(summary.get("n", 0)),
            }
            for dim, mean in summary.get("dimension_means", {}).items():
                metrics[f"qalis.{dim.lower()}_mean"] = mean

            mlflow.log_metrics(metrics, step=self._step)
            self._step += 1

            if self.log_artifacts:
                import tempfile, os
                with tempfile.TemporaryDirectory() as tmpdir:
                    csv_path = os.path.join(tmpdir, f"batch_{self._step}.csv")
                    batch_result.save(csv_path)
                    mlflow.log_artifact(csv_path, artifact_path="qalis_batches")

        except Exception as exc:
            logger.error("MLflowExporter.update error: %s", exc)

    def log_params(self, params: Dict[str, Any]) -> None:
        """
        Log arbitrary parameters to the active MLflow run.

        Useful for recording system configuration alongside quality metrics::

            exporter.log_params({
                "llm_provider": "openai",
                "model_version": "gpt-4o-2024-11-20",
                "nli_model": "cross-encoder/nli-deberta-v3-large",
                "domain": "customer_support",
            })
        """
        if not self._mlflow_available:
            return
        try:
            import mlflow
            mlflow.log_params(params)
        except Exception as exc:
            logger.error("MLflowExporter.log_params error: %s", exc)

    @property
    def step(self) -> int:
        """Current MLflow logging step counter."""
        return self._step
