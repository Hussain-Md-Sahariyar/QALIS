"""
QALIS Collectors Package
========================

Provides instrumentation classes that wrap LLM API calls and collect
raw metric signals across all four QALIS layers in real time.

Classes:
    QALISCollector       Main collector — wraps a single LLM interaction
    BatchCollector       Collects metrics over a batch of interactions
    StreamingCollector   Low-latency streaming-aware collector (IQ-2/IQ-3)
    LogCollector         Offline collector that replays stored request logs

Typical usage::

    from qalis.collectors import QALISCollector, CollectorConfig

    cfg = CollectorConfig(system_id="my-app", domain="customer_support")
    collector = QALISCollector(cfg)

    result = collector.collect(
        query="What is your return policy?",
        response="Our return window is 30 days...",
        context=["policy_document.txt excerpt..."],
    )
    print(result.summary())
"""

from qalis.collectors.collector import QALISCollector, CollectorConfig
from qalis.collectors.batch_collector import BatchCollector
from qalis.collectors.streaming_collector import StreamingCollector
from qalis.collectors.log_collector import LogCollector

__all__ = [
    "QALISCollector",
    "CollectorConfig",
    "BatchCollector",
    "StreamingCollector",
    "LogCollector",
]
