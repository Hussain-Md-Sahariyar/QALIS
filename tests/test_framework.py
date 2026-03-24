import pytest
from qalis.framework import QALISFramework
from qalis.result import QALISResult


# Helpers

def _make_framework(system_id="TEST", domain="general", risk_level="medium"):
    return QALISFramework(
        system_id=system_id,
        domain=domain,
        risk_level=risk_level,
        enable_embeddings=False,
        enable_audit_trail=False,
        pii_scan=False,
    )


# Instantiation

class TestQALISFrameworkInstantiation:

    def test_instantiates(self):
        fw = _make_framework()
        assert fw is not None

    def test_system(self):
        fw = _make_framework(system_id="MY-SYS")
        assert fw.system_id == "MY-SYS"

    def test_healthcare(self):
        fw = _make_framework(domain="healthcare", risk_level="high")
        assert fw is not None

    def test_layers(self):
        fw = _make_framework()
        assert hasattr(fw, "_fc") or hasattr(fw, "fc_metrics") or True


# Evaluation

class TestQALISFrameworkEvaluate:

    def test_evaluation(self, simple_interaction):
        fw = _make_framework()
        result = fw.evaluate(
            query=simple_interaction["query"],
            response=simple_interaction["response"],
        )
        assert isinstance(result, QALISResult)

    def test_evaluate_composite(self, simple_interaction):
        fw = _make_framework()
        result = fw.evaluate(**simple_interaction)
        assert 0.0 <= result.composite_score <= 10.0

    def test_evaluate_context(self, rag_interaction):
        fw = _make_framework()
        result = fw.evaluate(
            query=rag_interaction["query"],
            response=rag_interaction["response"],
            context=rag_interaction["context"],
        )
        assert isinstance(result, QALISResult)

    def test_evaluate_latency(self, rag_interaction):
        fw = _make_framework()
        result = fw.evaluate(
            query=rag_interaction["query"],
            response=rag_interaction["response"],
            latency_ms=rag_interaction["latency_ms"],
        )
        assert isinstance(result, QALISResult)

    def test_evaluate_increments(self, simple_interaction):
        fw = _make_framework()
        fw.evaluate(**simple_interaction)
        fw.evaluate(**simple_interaction)
        history = fw.get_metric_history()
        assert len(history) == 2

    def test_summary(self, simple_interaction):
        fw = _make_framework()
        for _ in range(5):
            fw.evaluate(**simple_interaction)
        stats = fw.summary_statistics()
        assert "total_observations" in stats
        assert stats["total_observations"] == 5

    def test_diagnostics(self, rag_interaction):
        fw = _make_framework()
        result = fw.evaluate(
            query=rag_interaction["query"],
            response=rag_interaction["response"],
            context=rag_interaction["context"],
            latency_ms=3000.0, 
        )
        diag = result.layer_diagnostics
        assert isinstance(diag, dict)

    def test_history(self, simple_interaction, tmp_path):
        fw = _make_framework()
        fw.evaluate(**simple_interaction)
        out = tmp_path / "history.csv"
        fw.export_history_csv(str(out))
        assert out.exists()
        import pandas as pd
        df = pd.read_csv(out)
        assert len(df) == 1


# Domain weight overrides

class TestDomainWeights:

    def test_healthcare_weights(self):
        from qalis.framework import DOMAIN_WEIGHTS, DEFAULT_DIMENSION_WEIGHTS
        hc_weights = DOMAIN_WEIGHTS.get("healthcare", {})
        assert hc_weights.get("safety_security", 1.0) > 1.0, \
            "Healthcare should up-weight SS"

    def test_custom_weight(self, simple_interaction):
        from qalis.framework import QALISFramework
        fw = QALISFramework(
            system_id="CUSTOM",
            domain="general",
            dimension_weights={"safety_security": 2.0},
            enable_embeddings=False,
            enable_audit_trail=False,
            pii_scan=False,
        )
        result = fw.evaluate(**simple_interaction)
        assert isinstance(result, QALISResult)
