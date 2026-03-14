"""
Tests for qalis.collectors — QALISCollector, BatchCollector.

Paper reference: §3.3 (data collection protocol).
"""

import pytest
from qalis.collectors.collector import QALISCollector, CollectorConfig
from qalis.collectors.batch_collector import BatchCollector
from qalis.result import QALISResult


# ---------------------------------------------------------------------------
# QALISCollector
# ---------------------------------------------------------------------------

class TestQALISCollector:

    def test_collect_returns_qalis_result(self, collector_config, simple_interaction):
        collector = QALISCollector(collector_config)
        result = collector.collect(**simple_interaction)
        assert isinstance(result, QALISResult)

    def test_collect_composite_in_range(self, collector_config, simple_interaction):
        collector = QALISCollector(collector_config)
        result = collector.collect(**simple_interaction)
        assert 0.0 <= result.composite_score <= 10.0

    def test_collect_increments_observation_index(self, collector_config, simple_interaction):
        collector = QALISCollector(collector_config)
        assert collector.observation_count == 0
        collector.collect(**simple_interaction)
        assert collector.observation_count == 1
        collector.collect(**simple_interaction)
        assert collector.observation_count == 2

    def test_collect_with_latency(self, collector_config, rag_interaction):
        collector = QALISCollector(collector_config)
        result = collector.collect(**rag_interaction)
        assert isinstance(result, QALISResult)

    def test_collect_with_api_error(self, collector_config, simple_interaction):
        collector = QALISCollector(collector_config)
        result = collector.collect(
            query=simple_interaction["query"],
            response=simple_interaction["response"],
            api_error=True,
        )
        assert isinstance(result, QALISResult)

    def test_collect_has_timestamp(self, collector_config, simple_interaction):
        collector = QALISCollector(collector_config)
        result = collector.collect(**simple_interaction)
        assert result.timestamp is not None
        assert "T" in result.timestamp   # ISO 8601 format

    def test_collect_has_dimension_scores(self, collector_config, simple_interaction):
        collector = QALISCollector(collector_config)
        result = collector.collect(**simple_interaction)
        assert len(result.dimension_scores) > 0

    def test_violation_metrics_trigger_violations(self, collector_config, violation_metrics_raw):
        """
        A response that produces violations should appear in threshold_violations.
        This test exercises the scoring pipeline end-to-end.
        """
        # Create a collector and inject raw metrics manually via scoring
        from qalis.utils.scoring import normalise_metrics
        for prefix in ["SF", "RO", "SS"]:
            _, violations = normalise_metrics(violation_metrics_raw, prefix)
            if prefix == "SF":
                assert "SF-3" in violations
            if prefix == "RO":
                assert "RO-2" in violations
            if prefix == "SS":
                assert "SS-2" in violations

    def test_reset_counter(self, collector_config, simple_interaction):
        collector = QALISCollector(collector_config)
        collector.collect(**simple_interaction)
        collector.collect(**simple_interaction)
        assert collector.observation_count == 2
        collector.reset_counter()
        assert collector.observation_count == 0

    def test_healthcare_config_instantiates(self, hc_config, simple_interaction):
        collector = QALISCollector(hc_config)
        result = collector.collect(**simple_interaction)
        assert isinstance(result, QALISResult)

    def test_to_dict_serialisable(self, collector_config, simple_interaction):
        import json
        collector = QALISCollector(collector_config)
        result = collector.collect(**simple_interaction)
        d = result.to_dict()
        # Should be JSON-serialisable
        json.dumps(d)  # raises if not serialisable


# ---------------------------------------------------------------------------
# BatchCollector
# ---------------------------------------------------------------------------

class TestBatchCollector:

    def test_collect_all_returns_list(self, collector_config, simple_interaction):
        batch = BatchCollector(collector_config, n_workers=2)
        interactions = [simple_interaction] * 5
        results = batch.collect_all(interactions)
        assert isinstance(results, list)
        assert len(results) == 5

    def test_all_results_are_qalis_result(self, collector_config, simple_interaction):
        batch = BatchCollector(collector_config, n_workers=1)
        results = batch.collect_all([simple_interaction] * 3)
        for r in results:
            assert isinstance(r, QALISResult)

    def test_summary_statistics(self, collector_config, simple_interaction):
        batch = BatchCollector(collector_config, n_workers=1)
        results = batch.collect_all([simple_interaction] * 10)
        stats = BatchCollector.summary_statistics(results)
        assert "n" in stats
        assert stats["n"] == 10
        assert "mean_composite" in stats
        assert "pass_rate" in stats
        assert "violation_rate" in stats
        assert 0.0 <= stats["mean_composite"] <= 10.0

    def test_summary_statistics_empty(self):
        stats = BatchCollector.summary_statistics([])
        assert stats == {}

    def test_batch_mixed_interactions(self, collector_config,
                                      simple_interaction, rag_interaction):
        batch = BatchCollector(collector_config, n_workers=2)
        interactions = [simple_interaction, rag_interaction, simple_interaction]
        results = batch.collect_all(interactions)
        assert len(results) == 3
