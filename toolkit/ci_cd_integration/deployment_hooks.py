from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# Exceptions

class QALISGateFailure(Exception):

    def __init__(
        self,
        message: str,
        failures: List[Dict[str, Any]],
        regressions: List[Dict[str, Any]],
        gate_result: Any,
    ):
        super().__init__(message)
        self.failures    = failures
        self.regressions = regressions
        self.gate_result = gate_result

    def __str__(self) -> str:
        parts = [f"QALIS gate failed — {len(self.failures)} failure(s)"]
        for f in self.failures:
            parts.append(
                f" {f['metric_id']}: {f['value']:.4f} "
                f"({f['operator']} {f['threshold']})"
            )
        for r in self.regressions:
            parts.append(
                f"  ↓ {r['metric_id']}: {r['delta']:+.4f} regression"
            )
        return "\n".join(parts)


# Deployment event record

@dataclass
class DeploymentEvent:
    """Record of a single deployment lifecycle event."""
    event_type: str   
    system_id: str
    timestamp: str
    trigger: str = ""    
    version: str = ""
    gate_passed: Optional[bool] = None
    gate_failures: List[str] = field(default_factory=list)
    gate_regressions: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type":        self.event_type,
            "system_id":         self.system_id,
            "timestamp":         self.timestamp,
            "trigger":           self.trigger,
            "version":           self.version,
            "gate_passed":       self.gate_passed,
            "gate_failures":     self.gate_failures,
            "gate_regressions":  self.gate_regressions,
            "notes":             self.notes,
        }


class DeploymentHooks:

    def __init__(
        self,
        system_id: str,
        config_path: str = "configs/ci_cd_config.yaml",
        compare_to: str = "last_stable_release",
        baseline_dir: str = "data/processed/baselines",
        event_log_path: str = "data/processed/deployment_event_log.jsonl",
        trigger: str = "",
        version: str = "",
        on_gate_failure: Optional[Callable[["QALISGateFailure"], None]] = None,
        dry_run: bool = False,
    ):
        self.system_id    = system_id
        self.config_path  = config_path
        self.compare_to   = compare_to
        self.baseline_dir = Path(baseline_dir)
        self.event_log    = Path(event_log_path)
        self.trigger      = trigger
        self.version      = version
        self._on_failure  = on_gate_failure
        self.dry_run      = dry_run
        self._gate_result: Any = None

        logger.info(
            "DeploymentHooks configured - system=%s trigger=%s version=%s dry_run=%s",
            system_id, trigger, version, dry_run,
        )

    # Internal helpers

    def _log_event(self, event: DeploymentEvent) -> None:

        if self.dry_run:
            return
        try:
            self.event_log.parent.mkdir(parents=True, exist_ok=True)
            with open(self.event_log, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(event.to_dict()) + "\n")
        except Exception as exc:
            logger.warning("Could not write deployment event log: %s", exc)

    def _baseline_path(self, tag: str) -> Path:
        return self.baseline_dir / f"{tag}_metrics.json"

    def _load_current_metrics(self) -> Optional[Dict[str, float]]:

        latest_path = Path("data/processed/aggregated/qalis_master_scores.csv")
        if not latest_path.exists():
            logger.debug("No master scores file found for baseline snapshot.")
            return None
        try:
            import pandas as pd
            df = pd.read_csv(latest_path)
            # Average each metric column across all systems
            numeric = df.select_dtypes("number")
            return {col: round(float(numeric[col].mean()), 4) for col in numeric.columns}
        except Exception as exc:
            logger.warning("Could not load current metrics for baseline: %s", exc)
            return None

    # Public API

    def pre_deploy(
        self,
        eval_sets: Optional[Dict[str, str]] = None,
        raise_on_failure: bool = True,
    ) -> bool:
        from toolkit.ci_gate.quality_gate import QALISQualityGate

        logger.info(
            "pre_deploy: running QALIS gate - system=%s compare_to=%s",
            self.system_id, self.compare_to,
        )
        gate = QALISQualityGate(
            system_id=self.system_id,
            config_path=self.config_path,
        )
        result = gate.run(eval_sets=eval_sets, compare_to=self.compare_to)
        self._gate_result = result

        event = DeploymentEvent(
            event_type="pre_deploy",
            system_id=self.system_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            trigger=self.trigger,
            version=self.version,
            gate_passed=result.passed,
            gate_failures=[f["metric_id"] for f in result.failures],
            gate_regressions=[r["metric_id"] for r in result.regressions],
        )
        self._log_event(event)

        if result.passed:
            logger.info("pre_deploy: QALIS gate PASSED - system=%s", self.system_id)
            return True

        logger.error("pre_deploy: QALIS gate FAILED — system=%s", self.system_id)
        logger.error(str(result))

        exc = QALISGateFailure(
            message=str(result),
            failures=result.failures,
            regressions=result.regressions,
            gate_result=result,
        )

        if self._on_failure:
            try:
                self._on_failure(exc)
            except Exception as cb_exc:
                logger.warning("on_gate_failure callback raised: %s", cb_exc)

        if raise_on_failure and not self.dry_run:
            raise exc

        return False

    def post_deploy(
        self,
        tag: str = "last_stable_release",
        metrics: Optional[Dict[str, float]] = None,
    ) -> None:
        if self.dry_run:
            logger.info("post_deploy: dry_run - baseline not saved.")
            return

        current = metrics or self._load_current_metrics()
        if not current:
            logger.warning("post_deploy: no metrics available - baseline not updated.")
            return

        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        baseline_file = self._baseline_path(tag)
        data = {
            "system_id":  self.system_id,
            "tag":        tag,
            "version":    self.version,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "metrics":    current,
        }
        with open(baseline_file, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        logger.info("post_deploy: baseline saved: %s", baseline_file)

        event = DeploymentEvent(
            event_type="post_deploy",
            system_id=self.system_id,
            timestamp=data["timestamp"],
            trigger=self.trigger,
            version=self.version,
            notes=f"Baseline '{tag}' updated with {len(current)} metrics.",
        )
        self._log_event(event)

    def on_deploy_failure(
        self,
        reason: str = "",
        rollback_version: Optional[str] = None,
    ) -> None:

        logger.error(
            "on_deploy_failure: deployment of %s (system=%s) failed - %s",
            self.version, self.system_id, reason,
        )
        event = DeploymentEvent(
            event_type="deploy_failure",
            system_id=self.system_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            trigger=self.trigger,
            version=self.version,
            notes=f"Reason: {reason}. Rollback to: {rollback_version or 'unknown'}.",
        )
        self._log_event(event)

    def load_event_log(self) -> List[DeploymentEvent]:
    
        if not self.event_log.exists():
            return []
        events: List[DeploymentEvent] = []
        with open(self.event_log, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    events.append(DeploymentEvent(**d))
                except Exception:
                    pass
        return events

    def gate_passed(self) -> Optional[bool]:
        """Return the result of the most recent pre_deploy() call, or None."""
        if self._gate_result is None:
            return None
        return self._gate_result.passed
