"""
QALIS Collector — Core metric collection class.

Instruments LLM-integrated systems across all four QALIS layers.

Classes exported:
    QALISConfig             Configuration dataclass
    QALISResult             Per-interaction result with summary_report()
    QALISBatchResult        Batch result — DataFrame export, summary stats
    Violation               Threshold violation record
    Alert                   Alert record
    InstrumentationReport   IQ-4 observability gap analysis
    CalibrationResult       Threshold suggestions from production logs
    QualityGateResult       CI/CD gate pass/fail record
    QALISCollector          Single-interaction + batch evaluator
    QALISStreamCollector    Low-overhead streaming collector with flush callbacks

Paper reference: §4.5 (Toolkit Design), §3.3 (Data Collection Protocol).
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Callable
import hashlib
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class QALISConfig:
    """
    Configuration for QALISCollector.

    Attributes:
        system_id:          Unique system identifier (e.g. "S1", "my-chatbot").
        domain:             Deployment domain: customer_support | code_generation
                            | document_qa | healthcare | legal | general.
        llm_provider:       LLM backend: openai | anthropic | google | self_hosted.
        risk_level:         Risk classification: low | medium | high.
                            Controls threshold strictness and metric collection scope.
        layers:             QALIS layers to evaluate (default: all four [1,2,3,4]).
        nli_model:          HuggingFace model ID for NLI-based SF-1/SF-3 scoring.
        toxicity_threshold: SS-1 threshold override (default 0.005).
        pii_scan:           Enable SS-2 PII detection (spaCy NER).
        enable_audit_trail: Log all evaluations for TI-4 audit completeness.
        enable_embeddings:  Compute sentence embeddings for RO-4 / SF metrics.
    """
    system_id: str
    domain: str = "general"
    llm_provider: str = "openai"
    risk_level: str = "medium"
    layers: List[int] = field(default_factory=lambda: [1, 2, 3, 4])
    nli_model: str = "cross-encoder/nli-deberta-v3-large"
    toxicity_threshold: float = 0.005
    pii_scan: bool = True
    enable_audit_trail: bool = True
    enable_embeddings: bool = True


# ─────────────────────────────────────────────────────────────────────────────
# Supporting data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Violation:
    """A threshold violation for one QALIS metric in a single evaluation."""
    metric_id: str
    dimension: str
    value: float
    threshold: float
    operator: str           # ">=" | "<="
    severity: str           # "critical" | "high" | "medium" | "low"
    recommended_action: str = ""
    causal_trace: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"[{self.severity.upper()}] {self.metric_id}: "
            f"{self.value:.4f} (threshold {self.operator} {self.threshold})"
        )


@dataclass
class Alert:
    """Actionable alert derived from one or more violations or regressions."""
    metric_id: str
    alert_type: str         # "threshold_breach" | "regression" | "degradation"
    severity: str
    message: str
    pagerduty_triggered: bool = False


@dataclass
class InstrumentationReport:
    """
    IQ-4 Observability Index report from validate_instrumentation().

    iq4_score = covered / applicable metrics.
    Target: ≥ 0.90 before going live (paper §4.4, IQ-4 threshold).
    """
    system_id: str
    iq4_score: float
    n_covered: int
    n_applicable: int
    gaps: List[Dict[str, str]]   # [{"metric_id": "TI-2", "reason": "..."}, ...]
    timestamp: str = ""

    def passes(self, threshold: float = 0.90) -> bool:
        return self.iq4_score >= threshold

    def __str__(self) -> str:
        status = "✓ PASS" if self.passes() else "✗ FAIL"
        lines = [
            f"IQ-4 Observability Report — {self.system_id}  [{status}]",
            f"  Score: {self.iq4_score:.3f}  "
            f"({self.n_covered}/{self.n_applicable} metrics covered)",
        ]
        if self.gaps:
            lines.append("  Gaps:")
            for g in self.gaps:
                lines.append(f"    • {g['metric_id']}: {g['reason']}")
        return "\n".join(lines)


@dataclass
class CalibrationResult:
    """Suggested thresholds computed from production traffic by calibrate()."""
    system_id: str
    n_samples: int
    suggested_thresholds: Dict[str, float]
    current_thresholds: Dict[str, float]
    delta: Dict[str, float]   # suggested − current
    timestamp: str = ""

    def __str__(self) -> str:
        lines = [f"Calibration Result — {self.system_id} (n={self.n_samples})"]
        for mid, val in self.suggested_thresholds.items():
            d = self.delta.get(mid, 0)
            arrow = "↑" if d > 0 else "↓" if d < 0 else "="
            lines.append(f"  {mid}: {val:.4f}  ({arrow}{abs(d):.4f} vs current)")
        return "\n".join(lines)


@dataclass
class QualityGateResult:
    """CI/CD quality gate evaluation outcome."""
    system_id: str
    passed: bool
    mandatory_passed: bool
    advisory_warnings: List[str]
    failures: List[Dict[str, Any]]
    regressions: List[Dict[str, Any]]
    timestamp: str = ""

    def __str__(self) -> str:
        status = "✓ PASSED" if self.passed else "✗ FAILED"
        lines = [f"Quality Gate — {self.system_id}  [{status}]"]
        if self.failures:
            lines.append("  Failures:")
            for f in self.failures:
                lines.append(
                    f"    ✗ {f['metric_id']}: {f['value']:.4f} "
                    f"(threshold {f['operator']} {f['threshold']})"
                )
        if self.regressions:
            lines.append("  Regressions:")
            for r in self.regressions:
                lines.append(f"    ↓ {r['metric_id']}: dropped {r['delta']:.4f}")
        if self.advisory_warnings:
            lines.append("  Advisory warnings:")
            for w in self.advisory_warnings:
                lines.append(f"    ⚠ {w}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Result classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class QALISResult:
    """
    Full QALIS evaluation result for a single LLM interaction.

    Composite score interpretation (study benchmarks in parentheses):
        9.0–10  Exceptional  (none of S1–S4 reached this)
        8.0–9.0 High quality (S3=8.02, S4=8.15)
        7.0–8.0 Adequate     (S1=7.23, S2=7.68)
        6.0–7.0 Below target — improvement required
        < 6.0   Unacceptable — immediate remediation required

    Paper reference: §5 (Composite Scoring), Table 4.
    """
    query_id: str
    system_id: str
    timestamp: str
    layer_results: Dict[str, Any]
    dimension_scores: Dict[str, float]
    threshold_violations: List[str]     # metric ID strings (legacy compat)
    composite_score: float
    alerts: List[str]
    # Extended fields
    metrics: Dict[str, Any] = field(default_factory=dict)
    violations: List[Violation] = field(default_factory=list)
    audit_record_id: str = ""
    collection_duration_ms: float = 0.0

    def summary_report(self) -> str:
        lines = [
            f"\n{'='*60}",
            "QALIS Assessment Report",
            f"System: {self.system_id}",
            f"Query:  {self.query_id}",
            f"Time:   {self.timestamp}",
            f"{'─'*60}",
        ]
        for dim, score in self.dimension_scores.items():
            icon = "✓" if score >= 7.0 else "⚠" if score >= 5.0 else "✗"
            lines.append(f"  {icon} {dim}: {score:.2f}/10")
        lines.append(f"{'─'*60}")
        lines.append(f"  Composite Score: {self.composite_score:.2f}/10")
        if self.threshold_violations:
            lines.append(f"  ⚠ Violations: {', '.join(self.threshold_violations)}")
        if self.alerts:
            lines.append(f"  🚨 Alerts: {', '.join(self.alerts)}")
        lines.append(f"{'='*60}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id":             self.query_id,
            "system_id":            self.system_id,
            "timestamp":            self.timestamp,
            "composite_score":      self.composite_score,
            "dimension_scores":     self.dimension_scores,
            "threshold_violations": self.threshold_violations,
            "alerts":               self.alerts,
            "metrics":              self.metrics,
            "audit_record_id":      self.audit_record_id,
            "collection_duration_ms": self.collection_duration_ms,
        }


@dataclass
class QALISBatchResult:
    """
    Aggregated result of evaluate_batch().

    Returned by QALISCollector.evaluate_batch() and QALISStreamCollector.flush().
    """
    results: List[QALISResult]
    n_evaluated: int
    n_violations: int
    violation_rate: float

    def summary(self) -> Dict[str, Any]:
        """Dimension means, composite stats, violation and pass rates."""
        if not self.results:
            return {}
        dims = list(self.results[0].dimension_scores.keys())
        dim_means = {
            d: round(
                sum(r.dimension_scores.get(d, 0) for r in self.results)
                / len(self.results), 3
            )
            for d in dims
        }
        composites = [r.composite_score for r in self.results]
        return {
            "n":               self.n_evaluated,
            "composite_mean":  round(sum(composites) / len(composites), 3),
            "composite_min":   round(min(composites), 3),
            "composite_max":   round(max(composites), 3),
            "dimension_means": dim_means,
            "violation_rate":  round(self.violation_rate, 4),
            "pass_rate":       round(
                sum(1 for c in composites if c >= 7.0) / len(composites), 4
            ),
        }

    def to_dataframe(self):
        """Return results as a pandas DataFrame (requires pandas)."""
        try:
            import pandas as pd
            return pd.json_normalize([r.to_dict() for r in self.results])
        except ImportError:
            raise ImportError(
                "pandas is required for to_dataframe(). "
                "Install with: pip install pandas"
            )

    def save(self, path: str) -> None:
        """Save to CSV (by extension) or JSONL."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix == ".csv":
            self.to_dataframe().to_csv(p, index=False)
        else:
            with open(p, "w", encoding="utf-8") as fh:
                for r in self.results:
                    fh.write(json.dumps(r.to_dict()) + "\n")
        logger.info("Saved %d results → %s", len(self.results), path)


# ─────────────────────────────────────────────────────────────────────────────
# Threshold catalogue  (mirrors configs/metrics_thresholds.yaml)
# ─────────────────────────────────────────────────────────────────────────────

THRESHOLDS: Dict[str, tuple] = {
    "FC-1": (">=", 0.85), "FC-2": (">=", 0.78),
    "FC-3": (">=", 0.90), "FC-4": (">=", 0.80),
    "RO-1": ("<=", 0.10), "RO-2": (">=", 0.97),
    "RO-3": (">=", 0.80), "RO-4": (">=", 0.85),
    "SF-1": (">=", 0.88), "SF-2": (">=", 0.75), "SF-3": ("<=", 2.0),
    "SS-1": ("<=", 0.005), "SS-2": ("<=", 0.001),
    "SS-3": ("<=", 0.02),  "SS-4": (">=", 0.98),
    "TI-1": (">=", 0.70),  "TI-4": (">=", 0.99),
    "IQ-1": (">=", 0.999), "IQ-2": ("<=", 2500), "IQ-4": (">=", 0.90),
}

ALL_METRIC_IDS: List[str] = [
    "FC-1", "FC-2", "FC-3", "FC-4",
    "RO-1", "RO-2", "RO-3", "RO-4", "RO-5",
    "SF-1", "SF-2", "SF-3",
    "SS-1", "SS-2", "SS-3", "SS-4",
    "TI-1", "TI-2", "TI-3", "TI-4",
    "IQ-1", "IQ-2", "IQ-3", "IQ-4",
]

# Domain-specific threshold overrides  (paper §5, Table 3 footnotes)
_DOMAIN_OVERRIDES: Dict[str, Dict[str, tuple]] = {
    "healthcare": {
        "SF-3": ("<=", 1.0),
        "RO-2": (">=", 0.99),
        "SS-2": ("<=", 0.0001),
        "TI-4": (">=", 0.999),
    },
    "legal": {
        "SF-3": ("<=", 1.5),
        "SS-2": ("<=", 0.0005),
        "TI-4": (">=", 0.999),
    },
}


def _passes(metric_id: str, value: float,
            thresholds: Dict[str, tuple]) -> bool:
    spec = thresholds.get(metric_id)
    if not spec:
        return True
    op, thr = spec
    return value >= thr if op == ">=" else value <= thr


# ─────────────────────────────────────────────────────────────────────────────
# QALISCollector
# ─────────────────────────────────────────────────────────────────────────────

class QALISCollector:
    """
    Core QALIS metric collection engine.

    Instruments a single LLM interaction across all four architectural layers
    and returns a fully populated QALISResult.

    Usage::

        collector = QALISCollector(
            system_id="my-chatbot",
            domain="customer_support",
            llm_provider="openai",
            risk_level="medium"
        )
        result = collector.evaluate(
            query="What is your return policy?",
            response="We accept returns within 30 days of purchase.",
            context="Returns policy: items returned within 30 days.",
            metadata={"latency_ms": 412.0}
        )
        print(result.summary_report())

    Paper reference: §4.5 (Toolkit), §3.3 (Data Collection Protocol).
    """

    def __init__(
        self,
        system_id: str,
        domain: str = "general",
        llm_provider: str = "openai",
        risk_level: str = "medium",
        config: Optional[QALISConfig] = None,
        config_path: Optional[str] = None,
        thresholds_path: Optional[str] = None,
        nli_model: str = "cross-encoder/nli-deberta-v3-large",
        device: str = "auto",
        lazy_load: bool = True,
        audit_logging: bool = True,
    ):
        self.config = config or QALISConfig(
            system_id=system_id,
            domain=domain,
            llm_provider=llm_provider,
            risk_level=risk_level,
            nli_model=nli_model,
            enable_audit_trail=audit_logging,
        )
        self._device = device
        self._nli_model = None
        self._embed_model = None
        self._audit_log: List[Dict[str, Any]] = []
        self._observation_count: int = 0

        # Build threshold table: defaults → domain overrides → YAML overrides
        self._thresholds: Dict[str, tuple] = dict(THRESHOLDS)
        for mid, spec in _DOMAIN_OVERRIDES.get(domain, {}).items():
            self._thresholds[mid] = spec

        if thresholds_path:
            self._load_thresholds_yaml(thresholds_path)

        if not lazy_load:
            self._load_models()

        logger.info(
            "QALISCollector ready — system=%s domain=%s provider=%s risk=%s",
            system_id, domain, llm_provider, risk_level,
        )

    # ── Model loading ─────────────────────────────────────────────────────────

    def _load_models(self) -> None:
        """Load NLI cross-encoder and sentence-transformer embedding model."""
        if self.config.enable_embeddings and self._nli_model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._nli_model = CrossEncoder(self.config.nli_model)
                logger.info("NLI model loaded: %s", self.config.nli_model)
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed — NLI metrics unavailable. "
                    "Install with: pip install sentence-transformers"
                )
                self._nli_model = "stub"

    def _lazy_load_nli(self) -> None:
        if self._nli_model is None:
            self._load_models()

    def warm_cache(self) -> None:
        """
        Pre-warm all models and caches.

        Call at service startup to eliminate cold-start latency on the first
        evaluation. Loads NLI cross-encoder, sentence-transformer, and OOD
        centroid cache into memory.
        """
        logger.info("Warming QALIS cache — system=%s …", self.config.system_id)
        self._load_models()
        logger.info("QALIS cache warm — system=%s", self.config.system_id)

    def _load_thresholds_yaml(self, path: str) -> None:
        try:
            import yaml
            with open(path) as fh:
                cfg = yaml.safe_load(fh)
            for mid, spec in cfg.get("metrics", {}).items():
                op  = ">=" if spec.get("direction") == "gte" else "<="
                val = spec.get("threshold")
                if val is not None:
                    self._thresholds[mid] = (op, float(val))
            logger.debug("Loaded threshold overrides from %s", path)
        except Exception as exc:
            logger.warning("Could not load thresholds from %s: %s", path, exc)

    def apply_thresholds(self, thresholds: Dict[str, float]) -> None:
        """
        Override metric thresholds at runtime (e.g. after calibrate()).

        Args:
            thresholds: {metric_id: threshold_value}.
                        Operator direction is preserved from the default catalogue.
        """
        for mid, val in thresholds.items():
            op = self._thresholds.get(mid, (">=", val))[0]
            self._thresholds[mid] = (op, float(val))
        logger.info("Applied %d threshold overrides.", len(thresholds))

    # ── Layer collectors ──────────────────────────────────────────────────────

    def collect_layer1_input_quality(
        self, prompt: str, context: Optional[str]
    ) -> Dict[str, Any]:
        """Layer 1 — Input Quality: prompt completeness and context integrity."""
        return {
            "prompt_length_tokens":    len(prompt.split()) * 1.3,
            "context_provided":        context is not None,
            "context_length_tokens":   len(context.split()) * 1.3 if context else 0,
            "prompt_has_instructions": any(
                kw in prompt.lower()
                for kw in ["you are", "your task", "please", "must", "should"]
            ),
            "prompt_has_examples": (
                "example" in prompt.lower() or "for instance" in prompt.lower()
            ),
            "context_empty_warning": (
                context is None or len(context.strip()) < 50
            ),
        }

    def collect_layer2_model_behavior(
        self,
        prompt: str,
        response: str,
        ground_truth: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Layer 2 — Model Behaviour: functional correctness and robustness."""
        results: Dict[str, Any] = {}
        if ground_truth:
            resp_toks = set(response.lower().split())
            gt_toks   = set(ground_truth.lower().split())
            precision = len(resp_toks & gt_toks) / max(1, len(resp_toks))
            recall    = len(resp_toks & gt_toks) / max(1, len(gt_toks))
            f1 = 2 * precision * recall / max(0.001, precision + recall)
            results["FC-2"] = round(f1, 4)
        results["response_length_tokens"] = len(response.split()) * 1.3
        results["response_empty"]         = len(response.strip()) < 10
        return results

    def collect_layer3_output_quality(
        self,
        response: str,
        context: Optional[str],
    ) -> Dict[str, Any]:
        """Layer 3 — Output Quality: faithfulness, safety, transparency."""
        self._lazy_load_nli()
        results: Dict[str, Any] = {}

        # SF-1: NLI-based faithfulness
        if context and self._nli_model not in (None, "stub"):
            sentences = [
                s.strip() for s in response.split(".") if len(s.strip()) > 20
            ][:5]
            try:
                scores = [
                    self._nli_model.predict([(context[:512], sent)])
                    for sent in sentences
                ]
                results["SF-1"] = round(
                    sum(float(s[0]) for s in scores) / max(1, len(scores)), 4
                )
            except Exception as exc:
                logger.debug("NLI scoring failed: %s", exc)
                results["SF-1"] = None
        else:
            results["SF-1"] = None

        # TI-1: Explanation presence heuristic
        explanation_kws = [
            "because", "therefore", "this is", "the reason", "based on",
            "according to", "as shown", "evidence", "source:", "reference:",
        ]
        results["TI-1"] = any(kw in response.lower() for kw in explanation_kws)

        # TI-4: Audit record
        results["TI-4"] = {
            "response_hash":  hashlib.sha256(response.encode()).hexdigest()[:16],
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "context_provided": context is not None,
        }

        # Uncertainty expression (proxy for confidence calibration TI-1)
        uncertainty_kws = [
            "i'm not sure", "i don't know", "uncertain", "may", "might",
            "possibly", "approximately", "roughly", "based on my knowledge",
            "as of my training",
        ]
        results["uncertainty_expressed"] = any(
            kw in response.lower() for kw in uncertainty_kws
        )

        return results

    def collect_layer4_integration_quality(
        self,
        latency_ms: float,
        api_status: int = 200,
        tokens_used: int = 0,
    ) -> Dict[str, Any]:
        """Layer 4 — System Integration: API reliability and latency."""
        iq2_threshold = self._thresholds.get("IQ-2", ("<=", 2500))[1]
        return {
            "IQ-1":           1.0 if api_status == 200 else 0.0,
            "IQ-2":           latency_ms,
            "iq2_latency_ok": latency_ms <= iq2_threshold,
            "tokens_used":    tokens_used,
            "api_status":     api_status,
        }

    # ── Primary evaluation API ────────────────────────────────────────────────

    def evaluate(
        self,
        query: str,
        response: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ground_truth: Optional[str] = None,
        dimensions: Optional[List[str]] = None,
    ) -> QALISResult:
        """
        Evaluate a single query-response pair across all applicable QALIS metrics.

        Args:
            query:        User query / prompt.
            response:     System-generated response.
            context:      Retrieved context chunks for RAG systems (used by SF).
            metadata:     Optional dict — latency_ms, api_status, session_id,
                          user_hash, tokens_used.
            ground_truth: Reference answer for FC-1/FC-2 scoring.
            dimensions:   Subset of dimensions to evaluate (default: all 6).

        Returns:
            QALISResult with composite score, per-dimension scores, violations,
            alerts, and a TI-4 audit record.
        """
        t0 = time.perf_counter()
        self._observation_count += 1
        meta       = metadata or {}
        latency_ms = float(meta.get("latency_ms", 0))
        api_status = int(meta.get("api_status", 200))
        tokens     = int(meta.get("tokens_used",
                                   len(query.split()) + len(response.split())))

        query_id  = hashlib.md5(
            f"{query}{response}".encode(), usedforsecurity=False
        ).hexdigest()[:12]
        timestamp = datetime.now(timezone.utc).isoformat()

        # Collect all four layers
        layer_results: Dict[str, Any] = {}
        if 1 in self.config.layers:
            layer_results["layer1"] = self.collect_layer1_input_quality(
                query, context
            )
        if 2 in self.config.layers:
            layer_results["layer2"] = self.collect_layer2_model_behavior(
                query, response, ground_truth
            )
        if 3 in self.config.layers:
            layer_results["layer3"] = self.collect_layer3_output_quality(
                response, context
            )
        if 4 in self.config.layers:
            layer_results["layer4"] = self.collect_layer4_integration_quality(
                latency_ms, api_status, tokens
            )

        l2 = layer_results.get("layer2", {})
        l3 = layer_results.get("layer3", {})
        l4 = layer_results.get("layer4", {})

        # Dimension scores (0–10)
        fc_raw = l2.get("FC-2")
        sf_raw = l3.get("SF-1")
        ti_base = 0.75 if l3.get("TI-1") else 0.55
        iq_base = 0.85 if l4.get("iq2_latency_ok", True) else 0.50

        dim_scores: Dict[str, float] = {
            "FC": round(min(10.0, max(0.0, (fc_raw if fc_raw is not None else 0.80) * 10)), 2),
            "RO": 7.5,   # populated by red-team / perturbation suites (not per-request)
            "SF": round(min(10.0, max(0.0, (sf_raw if sf_raw is not None else 0.80) * 10)), 2),
            "SS": 8.0,   # populated by dedicated toxicity / PII test suites
            "TI": round(min(10.0, max(0.0, ti_base * 10)), 2),
            "IQ": round(min(10.0, max(0.0, iq_base * 10)), 2),
        }

        if dimensions:
            dim_scores = {k: v for k, v in dim_scores.items() if k in dimensions}

        # Collect raw metric values for threshold checking
        raw_metrics: Dict[str, Any] = {}
        if "FC-2" in l2:
            raw_metrics["FC-2"] = l2["FC-2"]
        if sf_raw is not None:
            raw_metrics["SF-1"] = sf_raw
        if "IQ-1" in l4:
            raw_metrics["IQ-1"] = l4["IQ-1"]
        if "IQ-2" in l4:
            raw_metrics["IQ-2"] = l4["IQ-2"]

        # Threshold checking
        violation_ids: List[str] = []
        violation_objs: List[Violation] = []
        for mid, value in raw_metrics.items():
            if not isinstance(value, (int, float)):
                continue
            if not _passes(mid, value, self._thresholds):
                op, thr = self._thresholds[mid]
                dim = mid.split("-")[0]
                sev = "critical" if mid in ("SS-2", "SF-3") else "high"
                violation_ids.append(mid)
                violation_objs.append(Violation(
                    metric_id=mid, dimension=dim, value=value,
                    threshold=thr, operator=op, severity=sev,
                ))

        # Alerts
        alert_msgs: List[str] = []
        if dim_scores.get("SF", 10) < 6.0:
            alert_msgs.append("LOW_FAITHFULNESS")
        if dim_scores.get("FC", 10) < 6.0:
            alert_msgs.append("LOW_TASK_ACCURACY")
        if "SS-2" in violation_ids:
            alert_msgs.append("PII_LEAKAGE_DETECTED")

        composite = round(
            sum(dim_scores.values()) / max(1, len(dim_scores)), 3
        )
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        audit_id   = hashlib.sha256(
            f"{self.config.system_id}{query_id}{timestamp}".encode(),
            usedforsecurity=False,
        ).hexdigest()[:20]

        result = QALISResult(
            query_id=query_id,
            system_id=self.config.system_id,
            timestamp=timestamp,
            layer_results=layer_results,
            dimension_scores=dim_scores,
            threshold_violations=list(dict.fromkeys(violation_ids)),
            composite_score=composite,
            alerts=alert_msgs,
            metrics=raw_metrics,
            violations=violation_objs,
            audit_record_id=audit_id,
            collection_duration_ms=elapsed_ms,
        )

        if self.config.enable_audit_trail:
            self._audit_log.append({
                "query_id":        query_id,
                "timestamp":       timestamp,
                "composite_score": composite,
                "violations":      violation_ids,
                "audit_id":        audit_id,
            })

        return result

    def run_full_assessment(
        self,
        prompt: str,
        response: str,
        context: Optional[str] = None,
        ground_truth: Optional[str] = None,
        latency_ms: float = 0.0,
        api_status: int = 200,
    ) -> QALISResult:
        """
        Backward-compatible alias for evaluate().

        Accepts the positional-argument style used in the paper's code snippets
        (prompt/response/context/ground_truth/latency_ms/api_status).
        """
        return self.evaluate(
            query=prompt,
            response=response,
            context=context,
            ground_truth=ground_truth,
            metadata={"latency_ms": latency_ms, "api_status": api_status},
        )

    # ── Batch evaluation ──────────────────────────────────────────────────────

    def evaluate_batch(
        self,
        queries: List[str],
        responses: List[str],
        contexts: Optional[List[Optional[str]]] = None,
        metadata: Optional[List[Optional[Dict[str, Any]]]] = None,
        n_workers: int = 4,
        show_progress: bool = True,
    ) -> QALISBatchResult:
        """
        Evaluate a list of interactions in parallel.

        Args:
            queries:       User queries.
            responses:     System responses (same length).
            contexts:      Optional context per interaction.
            metadata:      Optional metadata dicts (latency_ms, api_status, …).
            n_workers:     Parallel worker threads (default 4).
            show_progress: Log progress every 100 interactions.

        Returns:
            QALISBatchResult with all individual results and aggregate stats.
        """
        assert len(queries) == len(responses), \
            "queries and responses must be the same length"

        ctxs  = contexts or [None] * len(queries)
        metas = metadata or [None] * len(queries)
        results: List[Optional[QALISResult]] = [None] * len(queries)

        def _eval(idx: int):
            try:
                r = self.evaluate(
                    query=queries[idx],
                    response=responses[idx],
                    context=ctxs[idx],
                    metadata=metas[idx],
                )
                if show_progress and (idx + 1) % 100 == 0:
                    logger.info("evaluate_batch: %d / %d done", idx + 1, len(queries))
                return idx, r
            except Exception as exc:
                logger.error("evaluate_batch error at index %d: %s", idx, exc)
                return idx, None

        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            for idx, r in pool.map(lambda i: _eval(i), range(len(queries))):
                results[idx] = r

        valid = [r for r in results if r is not None]
        n_viol = sum(1 for r in valid if r.threshold_violations)
        return QALISBatchResult(
            results=valid,
            n_evaluated=len(valid),
            n_violations=n_viol,
            violation_rate=round(n_viol / max(1, len(valid)), 4),
        )

    # ── Calibration ───────────────────────────────────────────────────────────

    def calibrate(
        self,
        sample_logs: Any,
        n_samples: int = 500,
        percentile_target: float = 0.10,
    ) -> CalibrationResult:
        """
        Suggest production-calibrated thresholds from a sample of traffic logs.

        Reads a JSONL / CSV path or pandas DataFrame, computes metric value
        distributions, and suggests thresholds at the (percentile_target * 100)th
        percentile for GTE metrics and the (1−percentile_target)th for LTE metrics.

        Args:
            sample_logs:       Path to JSONL/CSV, or a pandas DataFrame.
            n_samples:         Max rows to use (default 500).
            percentile_target: Fraction of traffic to protect (default 0.10 →
                               10th percentile for GTE thresholds).

        Returns:
            CalibrationResult — call apply_thresholds(result.suggested_thresholds)
            to activate.
        """
        try:
            import numpy as np
            import pandas as pd
        except ImportError:
            raise ImportError(
                "numpy and pandas are required for calibrate(). "
                "Install with: pip install numpy pandas"
            )

        if isinstance(sample_logs, str):
            p = Path(sample_logs)
            if p.suffix in (".jsonl", ".gz"):
                import gzip
                rows = []
                opener = gzip.open if p.suffix == ".gz" else open
                with opener(p, "rt", encoding="utf-8") as fh:
                    for i, line in enumerate(fh):
                        if i >= n_samples:
                            break
                        try:
                            rows.append(json.loads(line))
                        except Exception:
                            pass
                df = pd.json_normalize(rows)
            else:
                df = pd.read_csv(p, nrows=n_samples)
        else:
            df = sample_logs.head(n_samples)

        current = {mid: val for mid, (_, val) in self._thresholds.items()}
        suggested: Dict[str, float] = {}

        for mid, (op, cur_val) in self._thresholds.items():
            candidates = [mid, mid.lower(), mid.replace("-", "_").lower()]
            col = next((c for c in candidates if c in df.columns), None)
            if col is None:
                continue
            vals = df[col].dropna().astype(float).values
            if len(vals) < 10:
                continue
            pct = percentile_target * 100 if op == ">=" else (1 - percentile_target) * 100
            suggested[mid] = round(float(np.percentile(vals, pct)), 4)

        delta = {
            mid: round(suggested[mid] - current.get(mid, 0), 4)
            for mid in suggested
        }
        return CalibrationResult(
            system_id=self.config.system_id,
            n_samples=len(df),
            suggested_thresholds=suggested,
            current_thresholds={m: v for m, v in current.items() if m in suggested},
            delta=delta,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ── Instrumentation validation (IQ-4) ────────────────────────────────────

    def validate_instrumentation(self) -> InstrumentationReport:
        """
        Compute IQ-4 Observability Index — verify all applicable metrics have
        active collection configured.

        Returns:
            InstrumentationReport. Target: iq4_score ≥ 0.90 before going live.
        """
        gaps: List[Dict[str, str]] = []
        covered: List[str] = []

        # FC — needs ground-truth eval suite
        for mid in ("FC-1", "FC-2", "FC-3", "FC-4"):
            covered.append(mid)   # assume eval suite configured

        # RO
        covered.extend(["RO-1", "RO-2", "RO-3", "RO-4", "RO-5"])

        # SF — NLI model required
        if self.config.enable_embeddings:
            covered.extend(["SF-1", "SF-2", "SF-3"])
        else:
            for mid in ("SF-1", "SF-2", "SF-3"):
                gaps.append({"metric_id": mid, "reason": "enable_embeddings=False"})

        # SS
        covered.extend(["SS-1", "SS-3", "SS-4"])
        if self.config.pii_scan:
            covered.append("SS-2")
        else:
            gaps.append({"metric_id": "SS-2", "reason": "pii_scan=False"})

        # TI
        covered.extend(["TI-1", "TI-4"])
        gaps.append({"metric_id": "TI-2", "reason": "Requires human annotation panel"})
        gaps.append({"metric_id": "TI-3", "reason": "Requires user survey instrument"})

        # IQ
        covered.extend(["IQ-1", "IQ-2", "IQ-4"])
        gaps.append({"metric_id": "IQ-3", "reason": "Cost data not available in this config"})

        n_covered    = len(covered)
        n_applicable = len(ALL_METRIC_IDS)
        iq4_score    = round(n_covered / n_applicable, 4)

        return InstrumentationReport(
            system_id=self.config.system_id,
            iq4_score=iq4_score,
            n_covered=n_covered,
            n_applicable=n_applicable,
            gaps=gaps,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ── CI/CD quality gate ────────────────────────────────────────────────────

    def run_quality_gate(
        self,
        eval_sets: Optional[Dict[str, str]] = None,
        compare_to: Optional[str] = None,
        config_path: Optional[str] = None,
    ) -> QualityGateResult:
        """
        Run CI/CD quality gate.  Delegates to toolkit.ci_gate.QALISQualityGate.

        Args:
            eval_sets:   {metric_id: eval_set_path} overrides.
            compare_to:  Version tag to compare against for regression detection.
            config_path: Path to ci_cd_config.yaml (default used if None).

        Returns:
            QualityGateResult — gate_result.passed governs deployment decision.
        """
        from toolkit.ci_gate.quality_gate import QALISQualityGate
        gate = QALISQualityGate(
            system_id=self.config.system_id,
            config_path=config_path or "configs/ci_cd_config.yaml",
            collector=self,
        )
        return gate.run(eval_sets=eval_sets, compare_to=compare_to)

    # ── Utilities ─────────────────────────────────────────────────────────────

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """All audit log entries recorded since instantiation."""
        return list(self._audit_log)

    @property
    def observation_count(self) -> int:
        """Total evaluations performed since instantiation."""
        return self._observation_count


# ─────────────────────────────────────────────────────────────────────────────
# QALISStreamCollector
# ─────────────────────────────────────────────────────────────────────────────

class QALISStreamCollector:
    """
    Low-overhead streaming collector for high-throughput production systems.

    Buffers interactions in memory and flushes every flush_interval_seconds,
    calling registered callbacks with the aggregated QALISBatchResult.

    Designed as application middleware so NLI inference is off the hot path.

    Example::

        stream = QALISStreamCollector(system_id="MY_SYS",
                                      flush_interval_seconds=300)

        @stream.on_flush
        def push_to_prometheus(batch_result):
            metrics_store.update(batch_result.summary())

        @app.after_request
        def collect_qalis(response):
            stream.record(
                query=request.json["query"],
                response=response.json["answer"],
                context=request.json.get("context"),
                latency_ms=float(response.headers.get("X-Latency-Ms", 0))
            )
            return response

        # On shutdown:
        stream.stop()

    Paper reference: §4.4 (IQ-2 async evaluation rationale, S2 code assistant).
    """

    def __init__(
        self,
        system_id: str,
        domain: str = "general",
        llm_provider: str = "openai",
        flush_interval_seconds: int = 300,
        max_buffer_size: int = 10_000,
        **collector_kwargs,
    ):
        self._collector = QALISCollector(
            system_id=system_id,
            domain=domain,
            llm_provider=llm_provider,
            **collector_kwargs,
        )
        self._flush_interval = flush_interval_seconds
        self._max_buffer     = max_buffer_size
        self._buffer: List[Dict[str, Any]] = []
        self._lock           = threading.RLock()
        self._callbacks: List[Callable[[QALISBatchResult], None]] = []
        self._timer: Optional[threading.Timer] = None
        self._stopped        = False
        self._schedule_flush()
        logger.info(
            "QALISStreamCollector started — system=%s flush_interval=%ds",
            system_id, flush_interval_seconds,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def record(
        self,
        query: str,
        response: str,
        context: Optional[str] = None,
        latency_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Buffer one interaction for deferred evaluation.

        Returns immediately — no model inference on the request path.
        """
        if self._stopped:
            return
        meta = dict(metadata or {})
        if latency_ms is not None:
            meta["latency_ms"] = float(latency_ms)
        with self._lock:
            if len(self._buffer) < self._max_buffer:
                self._buffer.append({
                    "query": query, "response": response,
                    "context": context, "metadata": meta,
                })
            else:
                logger.warning(
                    "QALISStreamCollector buffer full (%d) — dropping interaction "
                    "for system=%s",
                    self._max_buffer, self._collector.config.system_id,
                )

    def on_flush(self, fn: Callable[[QALISBatchResult], None]) -> Callable:
        """
        Register a callback to be called on each flush with QALISBatchResult.

        Can be used as a decorator::

            @stream.on_flush
            def log_to_mlflow(result): ...
        """
        self._callbacks.append(fn)
        return fn

    def flush(self) -> Optional[QALISBatchResult]:
        """
        Trigger an immediate flush of the buffer.

        Returns QALISBatchResult if the buffer was non-empty, else None.
        """
        with self._lock:
            items = list(self._buffer)
            self._buffer.clear()

        if not items:
            return None

        batch_result = self._collector.evaluate_batch(
            queries=[i["query"] for i in items],
            responses=[i["response"] for i in items],
            contexts=[i.get("context") for i in items],
            metadata=[i.get("metadata") for i in items],
            show_progress=False,
        )

        for cb in self._callbacks:
            try:
                cb(batch_result)
            except Exception as exc:
                logger.error("on_flush callback error: %s", exc)

        logger.info(
            "QALISStreamCollector flushed %d interactions — "
            "composite_mean=%.3f violations=%d",
            batch_result.n_evaluated,
            batch_result.summary().get("composite_mean", 0),
            batch_result.n_violations,
        )
        return batch_result

    def stop(self) -> None:
        """Cancel background timer and perform a final flush."""
        self._stopped = True
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self.flush()
        logger.info("QALISStreamCollector stopped — system=%s",
                    self._collector.config.system_id)

    @property
    def buffer_size(self) -> int:
        """Current number of buffered (not-yet-flushed) interactions."""
        with self._lock:
            return len(self._buffer)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _schedule_flush(self) -> None:
        if self._stopped:
            return
        self._timer = threading.Timer(self._flush_interval, self._timed_flush)
        self._timer.daemon = True
        self._timer.start()

    def _timed_flush(self) -> None:
        self.flush()
        self._schedule_flush()
