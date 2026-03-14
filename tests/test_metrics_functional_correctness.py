"""
Tests for qalis.metrics.functional_correctness — FC-1 through FC-4.

Paper reference: §4.2, Table 3 (FC dimension).
"""

import pytest
from qalis.metrics.functional_correctness import FunctionalCorrectnessMetrics


@pytest.fixture
def fc_metrics():
    cfg = {
        "system_id": "TEST", "domain": "general",
        "risk_level": "medium", "enable_embeddings": False,
    }
    return FunctionalCorrectnessMetrics(cfg, risk_level="medium")


class TestFunctionalCorrectnessMetrics:

    def test_compute_returns_dict(self, fc_metrics, simple_interaction):
        result = fc_metrics.compute(
            query=simple_interaction["query"],
            response=simple_interaction["response"],
        )
        assert isinstance(result, dict)

    def test_fc1_present(self, fc_metrics, simple_interaction):
        result = fc_metrics.compute(
            query=simple_interaction["query"],
            response=simple_interaction["response"],
        )
        assert "FC-1" in result or any(k.startswith("FC") for k in result)

    def test_fc1_range(self, fc_metrics, rag_interaction):
        result = fc_metrics.compute(
            query=rag_interaction["query"],
            response=rag_interaction["response"],
            reference=rag_interaction.get("reference_answer"),
        )
        # All metric values should be in [0, 1] (raw proportions)
        for k, v in result.items():
            if v is not None and k.startswith("FC"):
                assert 0.0 <= v <= 1.0, f"{k}={v} out of [0,1]"

    def test_empty_response_does_not_crash(self, fc_metrics):
        result = fc_metrics.compute(query="test query", response="")
        assert isinstance(result, dict)

    def test_with_reference_answer(self, fc_metrics, rag_interaction):
        result = fc_metrics.compute(
            query=rag_interaction["query"],
            response=rag_interaction["response"],
            reference=rag_interaction["reference_answer"],
        )
        assert isinstance(result, dict)

    def test_rouge_l_helper(self, fc_metrics):
        """ROUGE-L should return 1.0 for identical strings."""
        score = fc_metrics._rouge_l("hello world", "hello world")
        assert score == pytest.approx(1.0, abs=0.01)

    def test_rouge_l_zero_for_no_overlap(self, fc_metrics):
        score = fc_metrics._rouge_l("abc", "xyz")
        assert score == pytest.approx(0.0, abs=0.01)

    def test_semantic_match_identical(self, fc_metrics):
        score = fc_metrics._semantic_match("return policy is 30 days",
                                           "return policy is 30 days")
        assert score >= 0.9

    def test_extract_claims_non_empty(self, fc_metrics):
        claims = fc_metrics._extract_claims(
            "The system scored 7.23. Detection lag improved by 68%."
        )
        assert isinstance(claims, list)
        assert len(claims) >= 1
