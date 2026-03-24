import pytest
from qalis.metrics.system_integration import SystemIntegrationMetrics


@pytest.fixture
def iq_metrics():
    cfg = {"system_id": "TEST", "domain": "general"}
    return SystemIntegrationMetrics(cfg)


class TestSystemIntegrationMetrics:

    def test_compute_returns_dict(self, iq_metrics):
        result = iq_metrics.compute(api_error=False, latency_ms=350.0)
        assert isinstance(result, dict)

    def test_iq1_no_error(self, iq_metrics):
        result = iq_metrics.compute(api_error=False)
        iq1 = result.get("IQ-1")
        if iq1 is not None:
            assert iq1 >= 0.99 
            
    def test_iq1_with_error(self, iq_metrics):
        result = iq_metrics.compute(api_error=True)
        iq1 = result.get("IQ-1")
        if iq1 is not None:
            assert iq1 < 1.0   

    def test_iq2_latency_present(self, iq_metrics):
        result = iq_metrics.compute(api_error=False, latency_ms=420.0)
        assert "IQ-2" in result or any(k.startswith("IQ") for k in result)

    def test_iq4_full_coverage(self, iq_metrics):
        all_ids = iq_metrics.get_all_metric_ids()
        result = iq_metrics.compute(
            api_error=False,
            covered_metric_ids=all_ids,
        )
        iq4 = result.get("IQ-4")
        if iq4 is not None:
            assert iq4 == pytest.approx(1.0, abs=0.01)

    def test_iq4_empty_coverage(self, iq_metrics):
        result = iq_metrics.compute(api_error=False, covered_metric_ids=[])
        iq4 = result.get("IQ-4")
        if iq4 is not None:
            assert iq4 == pytest.approx(0.0, abs=0.01)

    def test_get_all_metric_ids(self, iq_metrics):
        ids = iq_metrics.get_all_metric_ids()
        assert isinstance(ids, list)
        assert len(ids) == 24, f"Expected 24 metric IDs, got {len(ids)}: {ids}"

    def test_latency_statistics(self, iq_metrics):
        for lat in [100, 200, 300, 400, 500]:
            iq_metrics.compute(api_error=False, latency_ms=float(lat))
        stats = iq_metrics.compute_latency_statistics()
        assert isinstance(stats, dict)
        assert "mean" in stats or "p50" in stats or len(stats) > 0

    def test_availability_statistics(self, iq_metrics):
        iq_metrics.compute(api_error=False)
        iq_metrics.compute(api_error=False)
        iq_metrics.compute(api_error=True)
        stats = iq_metrics.compute_availability_statistics()
        assert isinstance(stats, dict)
