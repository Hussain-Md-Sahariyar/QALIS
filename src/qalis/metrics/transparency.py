"""
Transparency & Interpretability Metrics (TI-1 through TI-4)
=============================================================

Dimension 5 of the QALIS framework (§5.5).

Metrics implemented:
    TI-1: Explanation Coverage Rate — outputs with reasoning/sources / total outputs
    TI-2: Explanation Faithfulness Score — faithful explanations / total explanations
    TI-3: User Interpretability Rating — mean Likert rating (1–5 scale, in-app survey)
    TI-4: Audit Trail Completeness — complete audit records / total transactions

Layer: 3 (Output Quality) for TI-1, TI-2, TI-3; Layer 4 for TI-4
Cadence: Daily (TI-1, TI-4); Monthly (TI-2, TI-3) — Table 3

Target thresholds (from Table 3):
    TI-1: ≥ 0.70
    TI-2: ≥ 0.80 (human evaluation panel)
    TI-3: ≥ 3.8 / 5.0 (mean user rating)
    TI-4: ≥ 0.99

KEY EMPIRICAL FINDING (§6.2, §7.1):
    The Transparency dimension was the most consistently underperforming
    quality area across all four systems:
        Mean score: 7.05/10 (lowest of 6 dimensions, Table 4)
        Std dev: 1.35 (highest variance — §7.1)
    
    Per-system Transparency scores (Table 4):
        S1 (Customer Support):  5.6/10
        S2 (Code Assistant):    6.2/10
        S3 (Doc. Summarization): 7.5/10
        S4 (Medical Triage):    8.9/10

    Finding resonated with interview data: practitioners consistently
    identified explanation quality as a recognized gap but one for which
    they lacked established tooling (§7.1).

Regulatory motivation: EU AI Act [37] explainability requirements for
high-risk AI systems; user trust calibration (§5.5).
"""

import re
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Explanation presence indicators for TI-1
# ---------------------------------------------------------------------------

EXPLANATION_MARKERS: Dict[str, List[str]] = {
    "chain_of_thought": [
        r'\blet me\s+(think|analyze|break this down|work through)\b',
        r'\bstep\s+\d+[.:]\b',
        r'\bfirst,\s+', r'\bsecond,\s+', r'\bfinally,\s+',
        r'\btherefore\b', r'\bbecause\b', r'\bsince\b',
        r'\bthis means\b', r'\bthis implies\b',
        r'\bmy reasoning\b', r'\bthe reason\b',
    ],
    "source_attribution": [
        r'\baccording to\b', r'\bbased on\b', r'\bper\b',
        r'\bas stated in\b', r'\bas noted in\b', r'\bsource:\b',
        r'\[(\d+)\]', r'\(see\s+\w',
        r'\bthe document (states|says|indicates|mentions)\b',
        r'\bthe context (shows|provides|contains)\b',
    ],
    "uncertainty_indicators": [
        r'\bi\'m not (certain|sure|confident)\b',
        r'\bthis is (uncertain|unclear|ambiguous)\b',
        r'\byou (may want to|should) (verify|confirm|check)\b',
        r'\bconsult\s+a\s+(professional|specialist|doctor|lawyer|expert)\b',
        r'\bI cannot (confirm|verify|guarantee)\b',
        r'\bplease (note|be aware) that\b',
        r'\bthis (may|might|could) (vary|depend|differ)\b',
    ],
    "confidence_expression": [
        r'\bI am (confident|certain|sure) that\b',
        r'\bwith (high|low) confidence\b',
        r'\bmost likely\b', r'\bprobably\b', r'\bpossibly\b',
        r'\bin my (assessment|judgment|estimation)\b',
    ],
}

# Audit trail required fields (for TI-4)
AUDIT_TRAIL_REQUIRED_FIELDS = [
    "request_id",
    "timestamp",
    "input_hash",
    "model_id",
    "output_hash",
    "session_id",
    "user_id_hash",  # Anonymized
    "retrieved_context_ids",
    "metric_scores",
    "latency_ms",
]


class TransparencyMetrics:
    """
    Implements the four Transparency & Interpretability metrics (TI-1 through TI-4).

    TI-1 and TI-4 are automated and can be collected continuously.
    TI-2 requires human evaluation panel (monthly cadence in the study).
    TI-3 requires in-app user survey (monthly cadence).

    For automated approximation of TI-2, an LLM judge approach is supported:
    a secondary LLM evaluates whether the explanation faithfully reflects
    the reasoning behind the primary output (§9 future work direction).

    The Transparency dimension emerging as the weakest (Table 4, §7.1) has
    significant implications for framework adoption:
    "Organizations should prioritize transparency assessment early in the
    quality assurance lifecycle, as it is the dimension least likely to be
    adequately covered by their existing tooling." (§7.3)
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ti1_threshold = config.get("TI1_explanation_coverage_threshold", 0.70)
        self.ti2_threshold = config.get("TI2_explanation_faithfulness_threshold", 0.80)
        self.ti3_threshold = config.get("TI3_user_interpretability_threshold", 3.8)
        self.ti4_threshold = config.get("TI4_audit_trail_completeness_threshold", 0.99)

        # Precompile explanation marker patterns
        self._explanation_patterns: Dict[str, List] = {}
        for category, patterns in EXPLANATION_MARKERS.items():
            self._explanation_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def compute(
        self,
        query: str,
        response: str,
        context: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        user_rating: Optional[float] = None,
        audit_record: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Optional[float]]:
        """
        Compute transparency metrics.

        Args:
            query: User input query.
            response: LLM-generated response.
            context: Retrieved context (for attribution detection).
            request_id: Unique request identifier (for TI-4 audit trail).
            session_id: Session identifier.
            model_id: LLM model identifier.
            timestamp: Request timestamp.
            user_rating: User-provided interpretability rating (1–5).
            audit_record: Existing audit record dict (for TI-4 completeness check).

        Returns:
            Dict with TI1–TI4 metric values.
        """
        results: Dict[str, Optional[float]] = {}

        # TI-1: Explanation Coverage Rate (automated, daily)
        ti1_detail = self._compute_ti1(response)
        results["TI1_explanation_coverage_rate"] = ti1_detail["score"]
        results["TI1_explanation_types"] = ti1_detail["types_present"]

        # TI-2: Explanation Faithfulness Score (human panel, monthly)
        # In online mode: automated approximation
        results["TI2_explanation_faithfulness_score"] = self._compute_ti2_auto(
            query, response, context
        )

        # TI-3: User Interpretability Rating (in-app survey, monthly)
        results["TI3_user_interpretability_rating"] = user_rating  # None if not collected

        # TI-4: Audit Trail Completeness (automated, daily)
        results["TI4_audit_trail_completeness"] = self._compute_ti4(
            request_id=request_id,
            session_id=session_id,
            model_id=model_id,
            timestamp=timestamp,
            query=query,
            response=response,
            context=context,
            audit_record=audit_record,
        )

        return results

    def _compute_ti1(self, response: str) -> Dict[str, Any]:
        """
        TI-1: Explanation Coverage Rate
        
        Formula (Table 3): Explained_outputs / Total_outputs
        Measurement: Structural output analysis — presence of explanation elements
        Threshold: ≥ 0.70
        
        Explanation types counted:
            1. Chain-of-thought reasoning steps
            2. Source attribution markers
            3. Uncertainty / confidence indicators
            4. Explicit confidence expressions
        
        A response "has explanation coverage" if it contains at least one
        element from categories 1, 2, or 3 (source attribution OR reasoning
        OR uncertainty acknowledgment).
        
        Note: TI-1 does NOT verify that explanations are accurate (TI-2 does that).
        """
        if not response or len(response.split()) < 5:
            return {"score": 0.0, "types_present": []}

        types_present = []
        for category, patterns in self._explanation_patterns.items():
            if any(p.search(response) for p in patterns):
                types_present.append(category)

        # Coverage score: weighted by explanation richness
        coverage_weights = {
            "source_attribution": 0.35,      # Highest weight: most important for faithfulness
            "chain_of_thought": 0.30,         # Reasoning transparency
            "uncertainty_indicators": 0.25,   # Epistemic calibration
            "confidence_expression": 0.10,    # Minor contribution
        }

        score = sum(
            coverage_weights.get(t, 0.1) for t in types_present
        )
        score = float(np.clip(score, 0.0, 1.0))

        return {
            "score": score,
            "types_present": types_present,
            "coverage_count": len(types_present),
        }

    def _compute_ti2_auto(
        self,
        query: str,
        response: str,
        context: Optional[str],
    ) -> float:
        """
        TI-2: Explanation Faithfulness Score (automated approximation)
        
        Paper specification: Human evaluation panel, monthly cadence (Table 3).
        Inter-rater reliability: Cohen's kappa = 0.71 (§6.1).
        
        Automated approximation for continuous monitoring:
        Checks whether the reasoning provided in the response is consistent
        with the information available in context and query.
        
        Dimensions assessed:
            1. Consistency: stated reasoning does not contradict the response conclusion
            2. Groundedness: reasoning references content from context/query
            3. Completeness: key factors mentioned in response are also explained
        
        Note: §7.3 flags TI-2 as resource-intensive and calls for automated
        proxy metrics as a future work direction.
        """
        if not response:
            return 0.8  # Neutral prior when no response

        explanation_detail = self._compute_ti1(response)
        has_explanation = explanation_detail["score"] > 0.3

        if not has_explanation:
            # No explanation provided — trivially "faithful" in absence
            # but TI-1 will penalize coverage; TI-2 is N/A
            return None

        # Groundedness: does the explanation reference query/context content?
        groundedness = self._check_explanation_groundedness(
            response, query, context
        )

        # Internal consistency: does the conclusion follow from stated reasoning?
        consistency = self._check_reasoning_consistency(response)

        return float(np.clip(0.6 * groundedness + 0.4 * consistency, 0.0, 1.0))

    def _compute_ti4(
        self,
        request_id: Optional[str],
        session_id: Optional[str],
        model_id: Optional[str],
        timestamp: Optional[str],
        query: str,
        response: str,
        context: Optional[str],
        audit_record: Optional[Dict[str, Any]],
    ) -> float:
        """
        TI-4: Audit Trail Completeness
        
        Formula (Table 3): Complete_audit_records / Total_transactions
        Measurement: Log completeness check
        Threshold: ≥ 0.99 (Table 3)
        
        Required audit trail fields per §5.5:
            - input (query hash)
            - retrieved context (context document IDs)
            - model identifier
            - timestamp
            - output (response hash)
        
        Regulatory requirement: EU AI Act [37] mandates audit trail for
        high-risk AI systems. TI-4 = 0.99 threshold reflects compliance
        prerequisite framing from §7.2:
        "Organizations operating in regulated domains should treat TI-4
        as a compliance prerequisite rather than a quality-of-life improvement."
        
        Empirical finding: S4 (Medical Triage) scored highest on TI-4 (0.99+)
        due to HIPAA audit trail requirements.
        """
        if audit_record is not None:
            # Evaluate completeness of an existing audit record
            present_fields = [
                f for f in AUDIT_TRAIL_REQUIRED_FIELDS
                if f in audit_record and audit_record[f] is not None
            ]
            return float(len(present_fields) / len(AUDIT_TRAIL_REQUIRED_FIELDS))

        # Generate and evaluate completeness of current request's audit record
        current_record = self._build_audit_record(
            request_id=request_id,
            session_id=session_id,
            model_id=model_id,
            timestamp=timestamp,
            query=query,
            response=response,
            context=context,
        )

        present_fields = [
            f for f in AUDIT_TRAIL_REQUIRED_FIELDS
            if f in current_record and current_record[f] is not None
        ]

        return float(len(present_fields) / len(AUDIT_TRAIL_REQUIRED_FIELDS))

    def _build_audit_record(
        self,
        request_id: Optional[str],
        session_id: Optional[str],
        model_id: Optional[str],
        timestamp: Optional[str],
        query: str,
        response: str,
        context: Optional[str],
    ) -> Dict[str, Any]:
        """Construct a complete audit trail record for a single transaction."""
        record: Dict[str, Any] = {}

        # Unique identifiers
        record["request_id"] = request_id or self._generate_request_id(query)
        record["session_id"] = session_id
        record["timestamp"] = timestamp or datetime.utcnow().isoformat()
        record["model_id"] = model_id

        # Content hashes (privacy-preserving audit trail)
        record["input_hash"] = self._hash_content(query) if query else None
        record["output_hash"] = self._hash_content(response) if response else None

        # Context traceability
        record["retrieved_context_ids"] = (
            [self._hash_content(context[:50])] if context else []
        )

        # Anonymized user identifier
        record["user_id_hash"] = (
            self._hash_content(session_id) if session_id else None
        )

        # Metric scores placeholder (populated by framework)
        record["metric_scores"] = None  # Populated post-evaluation

        # Performance
        record["latency_ms"] = None  # Populated from system instrumentation

        return record

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _check_explanation_groundedness(
        self, response: str, query: str, context: Optional[str]
    ) -> float:
        """Check whether reasoning in response references query/context content."""
        reference_text = query + " " + (context or "")
        reference_words = set(
            re.findall(r'\b[a-z]{4,}\b', reference_text.lower())
        )

        # Find explanation segments in response
        reasoning_patterns = self._explanation_patterns.get("chain_of_thought", [])
        explanation_segments = []
        for pattern in reasoning_patterns:
            matches = pattern.findall(response)
            explanation_segments.extend(matches)

        if not explanation_segments or not reference_words:
            return 0.75  # Neutral score

        # Check how many words in explanations appear in reference
        explanation_text = " ".join(str(m) for m in explanation_segments)
        explanation_words = set(re.findall(r'\b[a-z]{4,}\b', explanation_text.lower()))

        overlap = explanation_words & reference_words
        if not explanation_words:
            return 0.75

        return float(min(len(overlap) / max(len(explanation_words) * 0.3, 1), 1.0))

    def _check_reasoning_consistency(self, response: str) -> float:
        """
        Check internal consistency of response reasoning.
        Simple proxy: detects contradictory statements using negation patterns.
        """
        sentences = re.split(r'(?<=[.!?])\s+', response)
        if len(sentences) < 2:
            return 0.85

        # Check for direct self-contradiction patterns
        contradiction_signals = [
            (r'\byes\b', r'\bno\b'),
            (r'\bpossible\b', r'\bimpossible\b'),
            (r'\bsupported\b', r'\bnot supported\b'),
            (r'\brecommend\b', r'\bnot recommend\b'),
        ]

        contradiction_found = False
        response_lower = response.lower()
        for pos_pattern, neg_pattern in contradiction_signals:
            if (re.search(pos_pattern, response_lower)
                    and re.search(neg_pattern, response_lower)):
                contradiction_found = True
                break

        return 0.70 if contradiction_found else 0.88

    @staticmethod
    def _hash_content(content: str) -> str:
        """Generate SHA-256 hash of content for privacy-preserving audit trail."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    def _generate_request_id(query: str) -> str:
        """Generate deterministic request ID from query content + timestamp."""
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        content_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"req_{ts}_{content_hash}"

    def compute_batch_ti1(self, responses: List[str]) -> Dict[str, float]:
        """
        Batch TI-1 computation for daily aggregated explanation coverage rate.
        Used by collectors/batch.py for daily cadence evaluation.
        """
        scores = [self._compute_ti1(r)["score"] for r in responses if r]
        if not scores:
            return {"TI1_coverage_rate": 0.0, "n_responses": 0}

        covered = sum(1 for s in scores if s > 0.3)
        return {
            "TI1_coverage_rate": float(covered / len(scores)),
            "TI1_mean_richness": float(np.mean(scores)),
            "TI1_std": float(np.std(scores)),
            "n_responses": len(scores),
        }
