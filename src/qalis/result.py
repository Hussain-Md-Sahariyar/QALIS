"""
QALIS Result data structures.

QALISResult encapsulates the output of a full QALIS evaluation pass,
including composite scores, per-dimension scores, raw metric values,
threshold violations, and cross-layer causal diagnostics.

These structures align with the data format used in the empirical study
reported in §6 of the QALIS paper, where 3,400 observations were collected
across four case systems.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class DimensionScore:
    """
    Represents the quality score for a single QALIS dimension.

    Attributes:
        name: Human-readable dimension name.
        score: Normalized score on 0–10 scale (aligned with Table 4).
        metrics: Dict of raw metric values for this dimension.
        layer: Architectural layer this dimension belongs to (1–4).
        weight: Dimension weight used in composite scoring.
        threshold_violations: Metric IDs within this dimension below threshold.
    """
    name: str
    score: float
    metrics: Dict[str, Any]
    layer: int
    weight: float = 1.0
    threshold_violations: List[str] = field(default_factory=list)

    def passed_threshold(self) -> bool:
        """Returns True if no threshold violations in this dimension."""
        return len(self.threshold_violations) == 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QALISResult:
    """
    Full QALIS evaluation result for a single LLM interaction.

    Composite QALIS Score interpretation (from empirical calibration):
        9.0–10.0: Exceptional quality; production-ready
        8.0–8.9: High quality; minor monitoring recommended
        7.0–7.9: Adequate quality; targeted improvement needed
        6.0–6.9: Below acceptable; improvement required
        < 6.0: Unacceptable; immediate remediation required

    Paper reference: §6.2–6.4, Table 4, and Figure 3.
    
    Case system benchmarks (from Table 4):
        S1 (Customer Support Chatbot):  7.23
        S2 (Code Assistant):            7.68
        S3 (Document Summarizer):       8.02
        S4 (Medical Triage Assistant):  8.15
        Overall Mean:                   7.77
    """
    system_id: str
    composite_score: float
    dimension_scores: Dict[str, DimensionScore]
    raw_metrics: Dict[str, Any]
    threshold_violations: List[str]
    layer_diagnostics: Dict[str, Any]
    evaluation_time_ms: float
    observation_index: int
    request_id: Optional[str] = None
    timestamp: Optional[str] = None

    def summary(self) -> str:
        """Return a human-readable single-line summary."""
        d = self.dimension_scores
        fc = d["functional_correctness"].score
        ro = d["robustness"].score
        sf = d["semantic_faithfulness"].score
        ss = d["safety_security"].score
        ti = d["transparency"].score
        iq = d["system_integration"].score

        def _check(score: float, dim: str) -> str:
            thresholds = {
                "fc": 7.0, "ro": 7.0, "sf": 8.0,
                "ss": 8.0, "ti": 6.5, "iq": 7.5
            }
            icon = "✓" if score >= thresholds.get(dim, 7.0) else "⚠"
            return f"{score:.1f}{icon}"

        violations_str = (
            f" | ⚡ Violations: {', '.join(self.threshold_violations)}"
            if self.threshold_violations else ""
        )

        return (
            f"QALIS Score: {self.composite_score:.2f}/10 "
            f"[FC:{_check(fc, 'fc')} RO:{_check(ro, 'ro')} "
            f"SF:{_check(sf, 'sf')} SS:{_check(ss, 'ss')} "
            f"TI:{_check(ti, 'ti')} IQ:{_check(iq, 'iq')}]"
            f"{violations_str}"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage/export."""
        return {
            "system_id": self.system_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "composite_score": self.composite_score,
            "observation_index": self.observation_index,
            "dimension_scores": {
                k: {
                    "score": v.score,
                    "layer": v.layer,
                    "weight": v.weight,
                    "violations": v.threshold_violations,
                }
                for k, v in self.dimension_scores.items()
            },
            "raw_metrics": self.raw_metrics,
            "threshold_violations": self.threshold_violations,
            "layer_diagnostics": self.layer_diagnostics,
            "evaluation_time_ms": self.evaluation_time_ms,
        }

    @property
    def quality_grade(self) -> str:
        """Map composite score to a quality grade."""
        if self.composite_score >= 9.0:
            return "A+"
        elif self.composite_score >= 8.5:
            return "A"
        elif self.composite_score >= 8.0:
            return "B+"
        elif self.composite_score >= 7.5:
            return "B"
        elif self.composite_score >= 7.0:
            return "C+"
        elif self.composite_score >= 6.5:
            return "C"
        elif self.composite_score >= 6.0:
            return "D"
        else:
            return "F"
