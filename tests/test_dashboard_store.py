import pytest
import threading
from qalis.dashboard.store import MetricsStore


@pytest.fixture
def store():
    return MetricsStore(max_history=100)


def _record(store, system_id="S1", composite=7.5, violations=None):
    store.record(
        system_id=system_id,
        composite=composite,
        dimension_scores={"FC": 7.8, "RO": 6.2},
        violations=violations or [],
        raw_metrics={}
    )


class TestMetricsStore:

    def test_returns(self, store):
        assert store.latest("S1") is None

    def test_latest(self, store):
        _record(store, composite=7.5)
        latest = store.latest("S1")
        assert latest is not None
        assert latest["composite"] == pytest.approx(7.5)

    def test_latest_returns(self, store):
        _record(store, composite=7.5)
        _record(store, composite=8.1)
        assert store.latest("S1")["composite"] == pytest.approx(8.1)

    def test_history_length(self, store):
        for i in range(5):
            _record(store, composite=float(i))
        history = store.history("S1", last_n=10)
        assert len(history) == 5

    def test_history_last(self, store):
        for i in range(20):
            _record(store, composite=float(i))
        history = store.history("S1", last_n=5)
        assert len(history) == 5

    def test_history_(self, store):
        for i in range(3):
            _record(store, composite=float(i))
        history = store.history("S1")
        composites = [h["composite"] for h in history]
        assert composites == [0.0, 1.0, 2.0]

    def test_systems_returns(self, store):
        _record(store, system_id="S1")
        _record(store, system_id="S2")
        _record(store, system_id="S3")
        assert store.systems() == {"S1", "S2", "S3"}

    def test_clear_single(self, store):
        _record(store, system_id="S1")
        _record(store, system_id="S2")
        store.clear("S1")
        assert store.latest("S1") is None
        assert store.latest("S2") is not None

    def test_clear_all(self, store):
        _record(store, system_id="S1")
        _record(store, system_id="S2")
        store.clear()
        assert store.systems() == set()

    def test_violation_summary(self, store):
        _record(store, system_id="S1", violations=["SF-3"])
        _record(store, system_id="S2", violations=[])
        summary = store.violation_summary()
        assert "S1" in summary
        assert "SF-3" in summary["S1"]

    def test_max_history(self):
        small_store = MetricsStore(max_history=5)
        for i in range(10):
            _record(small_store, composite=float(i))
        history = small_store.history("S1", last_n=100)
        assert len(history) == 5

    def test_thread_safety(self, store):
        errors = []
        def _writer():
            try:
                for i in range(50):
                    _record(store, composite=float(i % 10))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=_writer) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == [], f"Thread safety errors: {errors}"
        assert len(store.history("S1", last_n=200)) <= 100
