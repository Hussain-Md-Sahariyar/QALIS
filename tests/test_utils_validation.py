"""
Tests for qalis.utils.validation — CollectorConfig and interaction validation.
"""

import pytest
from qalis.utils.validation import validate_config, validate_interaction


# ---------------------------------------------------------------------------
# validate_config
# ---------------------------------------------------------------------------

class TestValidateConfig:

    def test_valid_config_passes(self, collector_config):
        validate_config(collector_config)  # should not raise

    def test_empty_system_id_raises(self, collector_config):
        collector_config.system_id = ""
        with pytest.raises(ValueError, match="system_id"):
            validate_config(collector_config)

    def test_invalid_risk_level_raises(self, collector_config):
        collector_config.risk_level = "critical"
        with pytest.raises(ValueError, match="risk_level"):
            validate_config(collector_config)

    def test_invalid_layer_raises(self, collector_config):
        collector_config.layers = [1, 2, 5]
        with pytest.raises(ValueError, match="layers"):
            validate_config(collector_config)

    def test_negative_weight_raises(self, collector_config):
        collector_config.dimension_weights["robustness"] = -0.5
        with pytest.raises(ValueError, match="dimension_weights"):
            validate_config(collector_config)

    def test_zero_weight_passes(self, collector_config):
        collector_config.dimension_weights["transparency"] = 0.0
        validate_config(collector_config)  # zero weight is allowed


# ---------------------------------------------------------------------------
# validate_interaction
# ---------------------------------------------------------------------------

class TestValidateInteraction:

    def test_valid_simple_interaction(self, simple_interaction):
        validate_interaction(simple_interaction)  # should not raise

    def test_valid_rag_interaction(self, rag_interaction):
        validate_interaction(rag_interaction)

    def test_missing_query_raises(self):
        with pytest.raises(ValueError, match="query"):
            validate_interaction({"response": "some answer"})

    def test_missing_response_raises(self):
        with pytest.raises(ValueError, match="response"):
            validate_interaction({"query": "some question"})

    def test_empty_query_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_interaction({"query": "   ", "response": "ok"})

    def test_non_string_query_raises(self):
        with pytest.raises(TypeError, match="query"):
            validate_interaction({"query": 42, "response": "ok"})

    def test_non_string_response_raises(self):
        with pytest.raises(TypeError, match="response"):
            validate_interaction({"query": "ok", "response": ["a", "b"]})

    def test_non_list_context_raises(self):
        with pytest.raises(TypeError, match="context"):
            validate_interaction({"query": "q", "response": "r", "context": "bad"})

    def test_non_string_context_chunk_raises(self):
        with pytest.raises(TypeError, match="context"):
            validate_interaction({"query": "q", "response": "r", "context": [123]})

    def test_negative_latency_raises(self):
        with pytest.raises(ValueError, match="latency_ms"):
            validate_interaction({"query": "q", "response": "r", "latency_ms": -10.0})

    def test_zero_latency_passes(self):
        validate_interaction({"query": "q", "response": "r", "latency_ms": 0.0})

    def test_none_context_passes(self):
        validate_interaction({"query": "q", "response": "r", "context": None})
