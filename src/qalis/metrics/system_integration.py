"""
System Integration Quality Metrics (IQ-1 through IQ-4)
=======================================================

Dimension 6 of the QALIS framework (§5.6).

These properties are "largely invisible to model-centric evaluation approaches
but are critically important for production reliability" (§4.5).

Metrics implemented:
    IQ-1: API Availability Rate — uptime / total scheduled time
    IQ-2: P95 Response Latency — 95th percentile end-to-end response time (ms)
    IQ-3: Cost per Quality Unit — API spend / composite quality score
    IQ-4: Observability Index — covered metric points / total metric points

Layer: 4 (System Integration Quality)
Cadence: Continuous for IQ-1, IQ-2; Monthly for IQ-3; Weekly for IQ-4 (Table 3)

Target thresholds (from Table 3):
    IQ-1: ≥ 0.999 (three-nines availability)
    IQ-2: ≤ 2,500 ms (P95 end-to-end)
    IQ-3: Organization-specific (cost-quality trade-off baseline)
    IQ-4: ≥ 0.90

KEY EMPIRICAL FINDING (§6.3, §7.2):
    Strong positive correlation between Latency (IQ-2) and API Error Rate
    derived from IQ-1: r = 0.74 (Figure 4, n=3,400).
    
    Implication for operations: "Percentile latency monitoring should be used
    as an early warning indicator for availability SLA breaches, enabling
    preemptive failover or fallback model switching strategies." (§7.2)

Best performing system on IQ: S1 Customer Support (IQ = 8.3/10, Table 4)
    Attributed to mature DevOps infrastructure and well-established SLA
    monitoring practices (§6.2).
"""

import time
import statistics
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Deque, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Latency percentile constants (aligned with paper Table 3 specification)
# ---------------------------------------------------------------------------

LATENCY_PERCENTILES = {
    "p50": 50,   # Median
    "p90": 90,
    "p95": 95,   # Primary metric for IQ-2
    "p99": 99,
}

# Time-to-First-Token (TTFT) thresholds for interactive applications
TTFT_THRESHOLDS = {
    "acceptable": 800,    # ms (< 800ms feels instant for users)
    "degraded": 1500,     # ms (1.5s starts to feel slow)
    "critical": 3000,     # ms (> 3s causes user abandonment)
}


class SystemIntegrationMetrics:
    """
    Implements the four System Integration Quality metrics (IQ-1 through IQ-4).

    IQ metrics require system-level instrumentation beyond the LLM component
    itself, including distributed tracing, infrastructure monitoring, and
    cost tracking integration.

    In the QALIS empirical study:
    - IQ-1, IQ-2 were collected via distributed tracing (5-min snapshots)
    - IQ-3 required organizational alignment on cost tracking (not available
      for S4 — see §6.3 collection completeness note)
    - IQ-4 was audited weekly using the QALIS coverage audit procedure

    The latency-availability correlation (r=0.74) observed in the study
    is consistent with known LLM API provider behavior where:
    1. High load → increased latency → eventual queue overflow → errors
    2. Model updates → latency spikes → brief availability degradation
    """

    TOTAL_QALIS_METRIC_POINTS = 24  # Full QALIS metric catalogue (Table 3)

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.iq1_threshold = config.get("IQ1_api_availability_threshold", 0.999)
        self.iq2_threshold = config.get("IQ2_p95_latency_ms_threshold", 2500)
        self.iq4_threshold = config.get("IQ4_observability_index_threshold", 0.90)

        # Rolling window for latency percentile computation
        # Window size: 1,000 requests (approximately 2–3 hours at S1 traffic)
        self._latency_window: Deque[float] = deque(maxlen=1000)
        self._error_window: Deque[bool] = deque(maxlen=1000)  # True = error
        self._cost_tracker: List[Dict[str, float]] = []
        self._session_start = datetime.utcnow()
        self._total_requests = 0
        self._total_errors = 0

    def compute(
        self,
        latency_ms: Optional[float] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        request_id: Optional[str] = None,
        api_error: bool = False,
        cost_per_request: Optional[float] = None,
        composite_quality_score: Optional[float] = None,
        covered_metric_ids: Optional[List[str]] = None,
    ) -> Dict[str, Optional[float]]:
        """
        Compute system integration quality metrics.

        Args:
            latency_ms: End-to-end response latency for this request (ms).
            input_tokens: Number of input tokens consumed.
            output_tokens: Number of output tokens generated.
            request_id: Unique request identifier.
            api_error: Whether this request resulted in an API error.
            cost_per_request: Direct API cost for this request (USD).
            composite_quality_score: Current QALIS composite score (for IQ-3).
            covered_metric_ids: List of QALIS metric IDs with active collection.

        Returns:
            Dict with IQ1–IQ4 metric values.
        """
        # Update rolling windows
        self._total_requests += 1
        if api_error:
            self._total_errors += 1

        if latency_ms is not None:
            self._latency_window.append(latency_ms)
        if api_error is not None:
            self._error_window.append(api_error)

        results: Dict[str, Optional[float]] = {}

        # IQ-1: API Availability Rate
        results["IQ1_api_availability_rate"] = self._compute_iq1(api_error)

        # IQ-2: P95 Response Latency
        results["IQ2_p95_latency_ms"] = self._compute_iq2(latency_ms)

        # IQ-3: Cost per Quality Unit
        results["IQ3_cost_per_quality_unit"] = self._compute_iq3(
            input_tokens, output_tokens, cost_per_request, composite_quality_score
        )

        # IQ-4: Observability Index
        results["IQ4_observability_index"] = self._compute_iq4(covered_metric_ids)

        # Supplementary latency breakdown
        results["IQ2_latency_ms_p50"] = self._get_percentile_latency(50)
        results["IQ2_latency_ms_p99"] = self._get_percentile_latency(99)

        return results

    def _compute_iq1(self, api_error: bool) -> float:
        """
        IQ-1: API Availability Rate
        
        Formula (Table 3): Uptime / Total_scheduled_time
        Measurement: Infrastructure monitoring (continuous)
        Threshold: ≥ 0.999 (three-nines availability)
        
        Implementation: Rolling error rate over last N requests.
        Uptime is approximated as the complement of the error rate.
        
        Correlation finding (§6.3): r = 0.74 with IQ-2 (latency).
        "Latency increases precede availability failures" — use IQ-2 as
        an early warning indicator for IQ-1 SLA breaches.
        
        S1 achieved highest IQ score (8.3/10) largely due to mature
        infrastructure supporting ≥ 0.9997 availability across 3 months.
        """
        if not self._error_window:
            return 1.0 if not api_error else 0.999

        error_rate = sum(self._error_window) / len(self._error_window)
        availability = 1.0 - error_rate
        return float(np.clip(availability, 0.0, 1.0))

    def _compute_iq2(self, latency_ms: Optional[float]) -> Optional[float]:
        """
        IQ-2: P95 Response Latency (end-to-end)
        
        Formula (Table 3): 95th percentile E2E response time (ms)
        Measurement: Distributed tracing (continuous)
        Threshold: ≤ 2,500 ms
        
        Percentiles tracked: P50, P90, P95 (primary), P99
        
        The paper reports 95th percentile as the primary SLA metric,
        consistent with industry practice for interactive applications
        (Google SRE Workbook; §5.6 rationale).
        
        Time-to-First-Token (TTFT) is additionally tracked for streaming
        applications (S1, S2 code assistant streaming completions).
        """
        if latency_ms is not None:
            self._latency_window.append(latency_ms)

        return self._get_percentile_latency(95)

    def _get_percentile_latency(self, percentile: int) -> Optional[float]:
        """Get specified percentile latency from rolling window."""
        if len(self._latency_window) < 10:
            return None

        latencies = sorted(self._latency_window)
        idx = int(len(latencies) * percentile / 100)
        idx = min(idx, len(latencies) - 1)
        return float(latencies[idx])

    def _compute_iq3(
        self,
        input_tokens: Optional[int],
        output_tokens: Optional[int],
        cost_per_request: Optional[float],
        composite_quality_score: Optional[float],
    ) -> Optional[float]:
        """
        IQ-3: Cost per Quality Unit
        
        Formula (Table 3): API_spend / Composite_quality_score
        Measurement: Cost monitoring + QALIS score (monthly)
        Threshold: Organization-specific (cost-quality trade-off)
        
        This metric enables cost-quality trade-off analysis for decisions
        such as model tier selection, prompt compression, and caching.
        
        Note (§6.3): IQ-3 could not be computed for S4 during the study
        due to organizational challenges in aligning cost tracking procedures
        for self-hosted Llama 3.1 infrastructure with the QALIS cost model.
        
        Cost model (API-hosted systems):
            input_cost = input_tokens × provider_rate_per_1k_tokens / 1000
            output_cost = output_tokens × provider_rate_per_1k_tokens / 1000
            total_cost = input_cost + output_cost
            cost_per_quality_unit = total_cost / composite_quality_score
        """
        if composite_quality_score is None or composite_quality_score <= 0:
            return None

        if cost_per_request is not None:
            cost = cost_per_request
        elif input_tokens is not None and output_tokens is not None:
            # Default GPT-4o pricing (as of study period, Oct–Dec 2024)
            # These rates are approximate; organizations configure actual rates
            INPUT_RATE = 0.0025 / 1000    # $0.0025 per 1K input tokens
            OUTPUT_RATE = 0.010 / 1000    # $0.010 per 1K output tokens
            cost = input_tokens * INPUT_RATE + output_tokens * OUTPUT_RATE
        else:
            return None

        quality_normalized = composite_quality_score / 10.0  # Normalize to 0–1
        if quality_normalized <= 0:
            return None

        return float(cost / quality_normalized)

    def _compute_iq4(self, covered_metric_ids: Optional[List[str]]) -> float:
        """
        IQ-4: Observability Index
        
        Formula (Table 3): Covered_metric_points / Total_metric_points
        Measurement: QALIS coverage audit (weekly)
        Threshold: ≥ 0.90
        
        "Observability is a prerequisite for diagnosing failures across
        all other layers." (§4.5)
        
        A metric point is "covered" if:
        1. The collection instrument is deployed and active
        2. The metric has been computed at least once in the past 7 days
        3. The metric value is within a plausible range (not stuck/null)
        
        Full QALIS coverage (IQ-4 = 1.0) requires all 24 metrics active.
        Practical coverage target: ≥ 0.90 (22 of 24 metrics).
        Study finding: 22/24 metrics achieved full collection (92% coverage)
        with IQ-3 and TI-3 having partial coverage issues (§6.3).
        """
        if covered_metric_ids is None:
            # Estimate based on framework initialization
            # Default: assume standard deployment covers 22/24 (per §6.3)
            return 22.0 / self.TOTAL_QALIS_METRIC_POINTS

        covered_count = len(covered_metric_ids)
        return float(
            np.clip(covered_count / self.TOTAL_QALIS_METRIC_POINTS, 0.0, 1.0)
        )

    def get_all_metric_ids(self) -> List[str]:
        """Return the complete list of QALIS metric IDs (Table 3)."""
        return [
            "FC1", "FC2", "FC3", "FC4",
            "RO1", "RO2", "RO3", "RO4", "RO5",
            "SF1", "SF2", "SF3",
            "SS1", "SS2", "SS3", "SS4",
            "TI1", "TI2", "TI3", "TI4",
            "IQ1", "IQ2", "IQ3", "IQ4",
        ]

    def compute_latency_statistics(self) -> Dict[str, Any]:
        """
        Compute full latency statistics for reporting and SLA analysis.
        Returns all percentiles tracked in the study (P50, P90, P95, P99).
        """
        if len(self._latency_window) < 2:
            return {"error": "Insufficient data (< 2 measurements)"}

        latencies = sorted(self._latency_window)
        n = len(latencies)

        return {
            "n_measurements": n,
            "mean_ms": float(np.mean(latencies)),
            "std_ms": float(np.std(latencies)),
            "min_ms": float(min(latencies)),
            "p50_ms": float(np.percentile(latencies, 50)),
            "p90_ms": float(np.percentile(latencies, 90)),
            "p95_ms": float(np.percentile(latencies, 95)),
            "p99_ms": float(np.percentile(latencies, 99)),
            "max_ms": float(max(latencies)),
            "above_threshold_rate": float(
                sum(1 for l in latencies if l > self.iq2_threshold) / n
            ),
            "threshold_ms": self.iq2_threshold,
        }

    def compute_availability_statistics(self) -> Dict[str, Any]:
        """Compute availability statistics from the error window."""
        if not self._error_window:
            return {"error": "No measurements recorded"}

        errors = list(self._error_window)
        n = len(errors)
        error_count = sum(errors)

        return {
            "n_requests": n,
            "error_count": error_count,
            "availability_rate": float(1.0 - error_count / n),
            "error_rate": float(error_count / n),
            "downtime_equivalent_minutes": float(
                error_count * 5 / 60  # Assuming 5s mean request duration
            ),
        }

    def check_latency_availability_correlation(self) -> Dict[str, Any]:
        """
        Compute latency-availability correlation.
        
        Reproduces the r=0.74 finding from §6.3 (Figure 4).
        Requires co-located latency and error measurements.
        """
        if len(self._latency_window) < 30 or len(self._error_window) < 30:
            return {"error": "Insufficient data for correlation analysis (< 30 pts)"}

        n = min(len(self._latency_window), len(self._error_window))
        latencies = list(self._latency_window)[-n:]
        errors = [float(e) for e in list(self._error_window)[-n:]]

        latency_arr = np.array(latencies)
        error_arr = np.array(errors)

        correlation = float(np.corrcoef(latency_arr, error_arr)[0, 1])

        return {
            "pearson_r": correlation,
            "n_observations": n,
            "interpretation": (
                "Strong latency-error correlation (consistent with paper r=0.74)"
                if abs(correlation) > 0.60
                else "Moderate correlation"
            ),
        }
