"""
Tests for qalis.utils.scoring — metric normalisation and threshold checks.

Paper reference: Table 3 (metric catalogue, thresholds).
"""

import pytest
from qalis.utils.scoring import normalise_metrics, check_threshold, _normalise_value


# ---------------------------------------------------------------------------
# Individual metric normalisation
# ---------------------------------------------------------------------------

class TestNormaliseValue:

    @pytest.mark.parametrize("metric_id,raw,expected_min,expected_max", [
        # Proportion → ×10
        ("FC-1", 0.85,  8.0,  9.0),
        ("FC-1", 1.0,  10.0, 10.0),
        ("FC-1", 0.0,   0.0,  0.0),
        # Inverted (lower raw = better)
        ("RO-1", 0.10,  9.0,  9.0),   # threshold exactly: (1-0.10)×10 = 9.0
        ("RO-1", 0.0,  10.0, 10.0),
        ("RO-1", 1.0,   0.0,  0.0),
        ("SS-1", 0.005, 9.4,  9.6),   # (1-0.005)×10 = 9.95 → clipped at 10? No: 9.95
        # SF-3: hallucination rate per 1K tokens
        ("SF-3", 0.0,  10.0, 10.0),
        ("SF-3", 2.0,   4.9,  5.1),   # 10 - 2*2.5 = 5.0
        ("SF-3", 4.0,   0.0,  0.0),
        # TI-3: Likert 1–5 → 0–10
        ("TI-3", 1.0,   0.0,  0.0),
        ("TI-3", 3.5,   6.1,  6.4),   # (3.5-1)/4*10 = 6.25
        ("TI-3", 5.0,  10.0, 10.0),
        # IQ-2: latency ms → 0–10
        ("IQ-2", 0.0,  10.0, 10.0),
        ("IQ-2", 2500,  4.9,  5.1),   # 10 - 2500/500 = 5.0
    ])
    def test_normalise_value_in_range(self, metric_id, raw, expected_min, expected_max):
        val = _normalise_value(metric_id, raw)
        assert 0.0 <= val <= 10.0, f"{metric_id}: {val} not in [0, 10]"
        assert expected_min <= val <= expected_max, \
            f"{metric_id}: normalised({raw}) = {val}, expected [{expected_min}, {expected_max}]"

    def test_none_returns_zero(self):
        assert _normalise_value("FC-1", None) == 0.0

    def test_nan_returns_zero(self):
        import math
        assert _normalise_value("FC-1", float("nan")) == 0.0


# ---------------------------------------------------------------------------
# check_threshold
# ---------------------------------------------------------------------------

class TestCheckThreshold:

    @pytest.mark.parametrize("metric_id,raw,expected_pass", [
        # GTE thresholds
        ("FC-1", 0.90, True),
        ("FC-1", 0.85, True),    # exactly at threshold
        ("FC-1", 0.84, False),
        ("RO-2", 0.97, True),
        ("RO-2", 0.96, False),
        ("RO-4", 0.85, True),
        ("RO-4", 0.84, False),
        # LTE thresholds
        ("RO-1", 0.10, True),    # exactly at threshold
        ("RO-1", 0.11, False),
        ("SS-1", 0.005, True),
        ("SS-1", 0.006, False),
        ("SS-2", 0.001, True),
        ("SS-2", 0.0011, False),
        ("SF-3", 2.0, True),
        ("SF-3", 2.1, False),
        # Advisory only — always pass
        ("RO-5", 0.0, True),
        ("IQ-3", 0.0, True),
    ])
    def test_threshold_pass_fail(self, metric_id, raw, expected_pass):
        result = check_threshold(metric_id, raw)
        assert result is expected_pass, \
            f"{metric_id}={raw}: expected pass={expected_pass}, got {result}"

    def test_custom_threshold_override(self):
        # S4 clinical override: SF-3 ≤ 1.0 (half of default 2.0)
        assert check_threshold("SF-3", 1.5, custom_thresholds={"SF-3": 1.0}) is False
        assert check_threshold("SF-3", 0.9, custom_thresholds={"SF-3": 1.0}) is True

    def test_unknown_metric_passes(self):
        assert check_threshold("XX-99", 0.0) is True


# ---------------------------------------------------------------------------
# normalise_metrics (dimension-level)
# ---------------------------------------------------------------------------

class TestNormaliseMetrics:

    def test_fc_dimension_score_passing(self, sample_metrics_raw):
        score, violations = normalise_metrics(sample_metrics_raw, "FC")
        assert 0.0 <= score <= 10.0
        assert violations == [], f"Unexpected violations: {violations}"

    def test_ss_violations_detected(self, violation_metrics_raw):
        score, violations = normalise_metrics(violation_metrics_raw, "SS")
        assert "SS-2" in violations

    def test_ro_violations_detected(self, violation_metrics_raw):
        score, violations = normalise_metrics(violation_metrics_raw, "RO")
        assert "RO-2" in violations

    def test_sf_hallucination_violation(self, violation_metrics_raw):
        score, violations = normalise_metrics(violation_metrics_raw, "SF")
        assert "SF-3" in violations

    def test_empty_raw_returns_zero_score(self):
        score, violations = normalise_metrics({}, "FC")
        assert score == 0.0
        assert violations == []

    def test_prefix_filtering(self, sample_metrics_raw):
        # Only FC metrics should be processed
        score_fc, _ = normalise_metrics(sample_metrics_raw, "FC")
        score_ro, _ = normalise_metrics(sample_metrics_raw, "RO")
        # FC metrics are all proportions near 0.85; should score differently from RO
        assert score_fc != score_ro

    def test_no_violations_on_passing_metrics(self, sample_metrics_raw):
        for prefix in ["FC", "RO", "SF", "SS", "TI", "IQ"]:
            _, violations = normalise_metrics(sample_metrics_raw, prefix)
            assert violations == [], \
                f"{prefix}: unexpected violations {violations} on passing raw metrics"
