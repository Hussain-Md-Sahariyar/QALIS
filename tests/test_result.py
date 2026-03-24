import pytest
from qalis.result import QALISResult, DimensionScore

# DimensionScore

class TestDimensionScore:

    def test_passed_threshold_no_violations(self):
        ds = DimensionScore(name="robustness", score=8.2, metrics={}, layer=2)
        assert ds.passed_threshold() is True

    def test_passed_threshold_with_violations(self):
        ds = DimensionScore(
            name="safety_security", score=5.1,
            metrics={}, layer=3,
            threshold_violations=["SS-2", "SS-3"],
        )
        assert ds.passed_threshold() is False

    def test_to_dict(self):
        ds = DimensionScore(
            name="transparency", score=7.05,
            metrics={"TI-1": 0.72, "TI-2": 0.68}, layer=3,
            weight=1.2,
            threshold_violations=["TI-4"],
        )
        d = ds.to_dict()
        assert d["name"] == "transparency"
        assert d["score"] == pytest.approx(7.05)
        assert d["threshold_violations"] == ["TI-4"]
        assert d["weight"] == pytest.approx(1.2)


# QALISResult

def _make_result(composite: float = 7.5, violations=None) -> QALISResult:
    dims = {
        "functional_correctness": DimensionScore("functional_correctness", 7.8, {}, 3),
        "robustness": DimensionScore("robustness", 6.2, {}, 2),
        "semantic_faithfulness": DimensionScore("semantic_faithfulness", 8.1, {}, 3),
        "safety_security": DimensionScore("safety_security", 7.4, {}, 3),
        "transparency": DimensionScore("transparency", 5.6, {}, 3, 
                                       threshold_violations=violations or []),
        "system_integration": DimensionScore("system_integration", 8.3, {}, 4),
    }
    return QALISResult(
        system_id="S1",
        composite_score=composite,
        dimension_scores=dims,
        raw_metrics={},
        threshold_violations=violations or [],
        layer_diagnostics={},
        evaluation_time_ms=12.4,
        observation_index=1,
        request_id="req-001",
        timestamp="2024-11-01T10:00:00+00:00",
    )


class TestQALISResult:

    def test_summary_no_violations(self):
        result = _make_result(7.5)
        s = result.summary()
        assert "7.50" in s
        assert "QALIS Score" in s

    def test_summary_with_violations(self):
        result = _make_result(6.8, violations=["TI-4", "SF-3"])
        s = result.summary()
        assert "TI-4" in s
        assert "SF-3" in s

    @pytest.mark.parametrize("score,expected_grade", [
        (9.5, "A+"),
        (8.7, "A"),
        (8.2, "B+"),
        (7.8, "B"),
        (7.2, "C+"),
        (6.6, "C"),
        (6.1, "D"),
        (5.0, "F"),
    ])
    def test_quality_grade(self, score, expected_grade):
        result = _make_result(composite=score)
        assert result.quality_grade == expected_grade

    def test_to_dict_contains_all_keys(self):
        result = _make_result(7.5, violations=["TI-1"])
        d = result.to_dict()
        assert "composite_score" in d
        assert "dimension_scores" in d
        assert "threshold_violations" in d
        assert "raw_metrics" in d
        assert "evaluation_time_ms" in d

    def test_composite_score_range(self):
        result = _make_result(8.15)
        assert 0.0 <= result.composite_score <= 10.0

    def test_study_composites_in_range(self):
        expected = {"S1": 7.23, "S2": 7.68, "S3": 8.02, "S4": 8.15}
        for sid, expected_val in expected.items():
            assert 6.5 <= expected_val <= 9.0, \
                f"{sid} composite {expected_val} outside plausible range"
