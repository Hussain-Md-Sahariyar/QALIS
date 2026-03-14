"""
Tests for qalis.metrics.semantic_faithfulness — SF-1 through SF-3.

Paper reference: §4.2, Table 3 (SF dimension).
"""

import pytest
from qalis.metrics.semantic_faithfulness import SemanticFaithfulnessMetrics


@pytest.fixture
def sf_metrics():
    cfg = {
        "system_id": "TEST", "domain": "general",
        "enable_embeddings": False,
    }
    return SemanticFaithfulnessMetrics(cfg, enable_nli=False)


class TestSemanticFaithfulnessMetrics:

    def test_compute_returns_dict(self, sf_metrics, rag_interaction):
        result = sf_metrics.compute(
            response=rag_interaction["response"],
            context=rag_interaction["context"],
            query=rag_interaction["query"],
        )
        assert isinstance(result, dict)

    def test_sf_keys_present(self, sf_metrics, rag_interaction):
        result = sf_metrics.compute(
            response=rag_interaction["response"],
            context=rag_interaction["context"],
            query=rag_interaction["query"],
        )
        sf_keys = [k for k in result if k.startswith("SF")]
        assert len(sf_keys) >= 1

    def test_sf1_range(self, sf_metrics, rag_interaction):
        result = sf_metrics.compute(
            response=rag_interaction["response"],
            context=rag_interaction["context"],
            query=rag_interaction["query"],
        )
        sf1 = result.get("SF-1")
        if sf1 is not None:
            assert 0.0 <= sf1 <= 1.0, f"SF-1={sf1} out of [0, 1]"

    def test_sf3_non_negative(self, sf_metrics, rag_interaction):
        result = sf_metrics.compute(
            response=rag_interaction["response"],
            context=rag_interaction["context"],
        )
        sf3 = result.get("SF-3")
        if sf3 is not None:
            assert sf3 >= 0.0, f"SF-3={sf3} is negative"

    def test_empty_context_no_crash(self, sf_metrics, simple_interaction):
        result = sf_metrics.compute(
            response=simple_interaction["response"],
            context=[],
            query=simple_interaction["query"],
        )
        assert isinstance(result, dict)

    def test_extract_atomic_claims(self, sf_metrics):
        text = (
            "The study included 14 participants. "
            "All four systems passed their respective thresholds. "
            "Detection lag improved by 68 percent."
        )
        claims = sf_metrics._extract_atomic_claims(text)
        assert isinstance(claims, list)
        assert len(claims) >= 2

    def test_split_to_sentences(self, sf_metrics):
        text = "First sentence. Second sentence! Third sentence?"
        sents = sf_metrics._split_to_sentences(text)
        assert len(sents) == 3

    def test_term_overlap_identical(self, sf_metrics):
        overlap = sf_metrics._term_overlap("hello world", "hello world")
        assert overlap == pytest.approx(1.0, abs=0.01)

    def test_term_overlap_no_shared_terms(self, sf_metrics):
        overlap = sf_metrics._term_overlap("alpha beta gamma", "delta epsilon zeta")
        assert overlap == pytest.approx(0.0, abs=0.01)

    def test_batch_sf3(self, sf_metrics):
        responses = [
            "The sky is blue and the grass is green.",
            "Water boils at 100 degrees Celsius at sea level.",
        ]
        results = sf_metrics.compute_batch_sf3(responses, context=[])
        assert isinstance(results, list)
        assert len(results) == 2
        for r in results:
            assert r >= 0.0
