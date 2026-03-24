"""
QALISCollector — Main real-time metric collection class.

Wraps a single LLM interaction and collects all applicable QALIS metrics
across the four architectural layers, returning a QALISResult.

Paper reference: §3.3 (data collection protocol), §4.2 (metric definitions).
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from qalis.metrics.functional_correctness import FunctionalCorrectnessMetrics
from qalis.metrics.robustness import RobustnessMetrics
from qalis.metrics.semantic_faithfulness import SemanticFaithfulnessMetrics
from qalis.metrics.safety_security import SafetySecurityMetrics
from qalis.metrics.transparency import TransparencyMetrics
from qalis.metrics.system_integration import SystemIntegrationMetrics
from qalis.result import QALISResult, DimensionScore

logger = logging.getLogger(__name__)

# Default dimension weights (equal weighting; paper §5 justification)
_DEFAULT_WEIGHTS: Dict[str, float] = {
    "functional_correctness": 1.0,
    "robustness": 1.0,
    "semantic_faithfulness": 1.0,
    "safety_security": 1.0,
    "transparency": 1.0,
    "system_integration": 1.0,
}

# Domain-specific threshold overrides (from Table 3 + practitioner interviews)
_DOMAIN_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "healthcare": {
        "sf3_threshold": 1.0,   # halved vs default 2.0 (S4 clinical override)
        "ro2_threshold": 0.99,  # tightened vs default 0.97
        "ss2_threshold": 0.0001,
        "ti1_threshold": 0.95,
    },
    "legal": {
        "sf3_threshold": 1.5,
        "ss2_threshold": 0.0005,
        "ti1_threshold": 0.90,
    },
    "gdpr": {
        "ss2_threshold": 0.0005,
    },
}


@dataclass
class CollectorConfig:
    """
    Configuration for QALISCollector.

    Attributes:
        system_id:          Unique identifier for the LLM system (e.g. "S1").
        domain:             Deployment domain. Triggers threshold overrides when
                            set to 'healthcare', 'legal', 'gdpr', etc.
        risk_level:         'low' | 'medium' | 'high'. Affects which metrics
                            are collected and at what precision.
        layers:             QALIS layers to evaluate (default: all four).
        nli_model:          HuggingFace model ID for NLI-based SF-3 scoring.
        enable_embeddings:  Whether to compute sentence embeddings (RO-4, SF-1).
        enable_audit_trail: Whether to emit TI-4 audit records.
        pii_scan:           Whether to run SS-2 PII detection.
        dimension_weights:  Per-dimension composite weights (default: equal).
        custom_thresholds:  Override any threshold from configs/metrics_thresholds.yaml.
    """

    system_id: str
    domain: str = "general"
    risk_level: str = "medium"
    layers: List[int] = field(default_factory=lambda: [1, 2, 3, 4])
    nli_model: str = "cross-encoder/nli-deberta-v3-large"
    enable_embeddings: bool = True
    enable_audit_trail: bool = True
    pii_scan: bool = True
    dimension_weights: Dict[str, float] = field(
        default_factory=lambda: dict(_DEFAULT_WEIGHTS)
    )
    custom_thresholds: Dict[str, float] = field(default_factory=dict)


class QALISCollector:
    """
    Real-time QALIS metric collector for a single LLM-integrated system.

    Instantiate once per system deployment, then call ``collect()`` for
    each LLM interaction. Thread-safe for concurrent request handling.

    Example::

        cfg = CollectorConfig(system_id="prod-chatbot", domain="customer_support")
        collector = QALISCollector(cfg)

        result = collector.collect(
            query="How do I return a product?",
            response="Returns are accepted within 30 days...",
            context=["Our return policy states..."],
            latency_ms=420.0,
        )
        if result.threshold_violations:
            send_alert(result)

    Attributes:
        config:     CollectorConfig instance.
        _obs_idx:   Running count of observations (for longitudinal tracking).
    """

    def __init__(self, config: CollectorConfig) -> None:
        self.config = config
        self._obs_idx: int = 0

        # Merge domain-specific threshold overrides
        thresholds = dict(_DOMAIN_THRESHOLDS.get(config.domain, {}))
        thresholds.update(config.custom_thresholds)

        metric_cfg: Dict[str, Any] = {
            "system_id": config.system_id,
            "domain": config.domain,
            "risk_level": config.risk_level,
            "nli_model": config.nli_model,
            "enable_embeddings": config.enable_embeddings,
            "enable_audit_trail": config.enable_audit_trail,
            "pii_scan": config.pii_scan,
            **thresholds,
        }

        # Instantiate dimension metric classes
        self._fc = FunctionalCorrectnessMetrics(metric_cfg, risk_level=config.risk_level)
        self._ro = RobustnessMetrics(metric_cfg, risk_level=config.risk_level)
        self._sf = SemanticFaithfulnessMetrics(metric_cfg, enable_nli=True)
        self._ss = SafetySecurityMetrics(
            metric_cfg,
            risk_level=config.risk_level,
            enable_pii_scan=config.pii_scan,
        )
        self._ti = TransparencyMetrics(metric_cfg)
        self._iq = SystemIntegrationMetrics(metric_cfg)

        logger.info(
            "QALISCollector initialised: system=%s domain=%s layers=%s",
            config.system_id,
            config.domain,
            config.layers,
        )

    # ------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------

    def collect(
        self,
        query: str,
        response: str,
        *,
        context: Optional[List[str]] = None,
        reference_answer: Optional[str] = None,
        latency_ms: Optional[float] = None,
        api_error: bool = False,
        token_cost: Optional[float] = None,
        covered_metric_ids: Optional[List[str]] = None,
        request_id: Optional[str] = None,
    ) -> QALISResult:
        """
        Collect QALIS metrics for one LLM interaction.

        Args:
            query:               The user query / prompt submitted to the system.
            response:            The system's response.
            context:             Retrieved context chunks (RAG). Used for SF-1,
                                 SF-2, SF-3 grounding checks.
            reference_answer:    Gold-standard answer for FC-1 accuracy scoring.
            latency_ms:          End-to-end latency in milliseconds (IQ-2).
            api_error:           True if the API returned an error (IQ-1).
            token_cost:          Token cost in USD for this request (IQ-3).
            covered_metric_ids:  Metric IDs instrumented in this run (IQ-4).
            request_id:          Caller-supplied request identifier.

        Returns:
            QALISResult with composite score, dimension scores, raw metrics,
            threshold violations, and layer diagnostics.
        """
        t0 = time.perf_counter()
        self._obs_idx += 1
        ts = datetime.now(timezone.utc).isoformat()

        raw: Dict[str, Any] = {}
        dim_scores: Dict[str, DimensionScore] = {}
        violations: List[str] = []
        layer_diag: Dict[str, Any] = {}

        # ── Layer 1+2: Input & Model Behavior ─────────────────────────────
        if 1 in self.config.layers or 2 in self.config.layers:
            ro_raw = self._ro.compute(query=query, response=response)
            raw["RO"] = ro_raw
            ro_score, ro_viol = self._score_dimension(ro_raw, "RO")
            dim_scores["robustness"] = DimensionScore(
                name="robustness", score=ro_score,
                metrics=ro_raw, layer=1,
                weight=self.config.dimension_weights.get("robustness", 1.0),
                threshold_violations=ro_viol,
            )
            violations.extend(ro_viol)
            layer_diag["layer_1_2"] = {"status": "ok" if not ro_viol else "violation"}

        # ── Layer 3: Output Quality ────────────────────────────────────────
        if 3 in self.config.layers:
            fc_raw = self._fc.compute(
                query=query, response=response, reference=reference_answer
            )
            sf_raw = self._sf.compute(
                response=response, context=context or [], query=query
            )
            ss_raw = self._ss.compute(query=query, response=response)
            ti_raw = self._ti.compute(
                query=query, response=response, context=context or []
            )
            raw.update({"FC": fc_raw, "SF": sf_raw, "SS": ss_raw, "TI": ti_raw})

            for key, raw_d, dim_name, layer in [
                ("FC", fc_raw, "functional_correctness", 3),
                ("SF", sf_raw, "semantic_faithfulness", 3),
                ("SS", ss_raw, "safety_security", 3),
                ("TI", ti_raw, "transparency", 3),
            ]:
                score, viol = self._score_dimension(raw_d, key)
                dim_scores[dim_name] = DimensionScore(
                    name=dim_name, score=score,
                    metrics=raw_d, layer=layer,
                    weight=self.config.dimension_weights.get(dim_name, 1.0),
                    threshold_violations=viol,
                )
                violations.extend(viol)

            layer_diag["layer_3"] = {
                "status": "ok" if not any(
                    v for k in ["FC","SF","SS","TI"]
                    for v in dim_scores.get(
                        {"FC":"functional_correctness","SF":"semantic_faithfulness",
                         "SS":"safety_security","TI":"transparency"}[k],
                        DimensionScore("",0,{},3)
                    ).threshold_violations
                ) else "violation"
            }

        # ── Layer 4: System Integration Quality ───────────────────────────
        if 4 in self.config.layers:
            iq_raw = self._iq.compute(
                api_error=api_error,
                latency_ms=latency_ms,
                token_cost=token_cost,
                covered_metric_ids=covered_metric_ids or [],
            )
            raw["IQ"] = iq_raw
            iq_score, iq_viol = self._score_dimension(iq_raw, "IQ")
            dim_scores["system_integration"] = DimensionScore(
                name="system_integration", score=iq_score,
                metrics=iq_raw, layer=4,
                weight=self.config.dimension_weights.get("system_integration", 1.0),
                threshold_violations=iq_viol,
            )
            violations.extend(iq_viol)
            layer_diag["layer_4"] = {"status": "ok" if not iq_viol else "violation"}

        composite = self._composite_score(dim_scores)
        eval_ms = (time.perf_counter() - t0) * 1000.0

        return QALISResult(
            system_id=self.config.system_id,
            composite_score=composite,
            dimension_scores=dim_scores,
            raw_metrics=raw,
            threshold_violations=list(dict.fromkeys(violations)),  # deduplicate
            layer_diagnostics=layer_diag,
            evaluation_time_ms=round(eval_ms, 2),
            observation_index=self._obs_idx,
            request_id=request_id,
            timestamp=ts,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_dimension(
        self, raw: Dict[str, Any], prefix: str
    ) -> tuple[float, List[str]]:
        """
        Normalise raw metric values to a 0–10 dimension score and
        identify threshold violations.

        Normalisation is metric-specific and defined in Table 3 of the paper.
        """
        from qalis.utils.scoring import normalise_metrics
        return normalise_metrics(raw, prefix)

    def _composite_score(self, dim_scores: Dict[str, DimensionScore]) -> float:
        """Weighted mean of dimension scores (default: equal weights)."""
        if not dim_scores:
            return 0.0
        total_w = sum(d.weight for d in dim_scores.values())
        if total_w == 0:
            return 0.0
        return round(
            sum(d.score * d.weight for d in dim_scores.values()) / total_w, 3
        )

    @property
    def observation_count(self) -> int:
        """Number of interactions evaluated since instantiation."""
        return self._obs_idx

    def reset_counter(self) -> None:
        """Reset the observation index (e.g. between test runs)."""
        self._obs_idx = 0
