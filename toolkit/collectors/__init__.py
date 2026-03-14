"""
QALIS Toolkit — Collectors
===========================

Core metric collection classes for instrumenting LLM-integrated systems.

Classes:
    QALISCollector        Single-interaction evaluator (batch / offline / online)
    QALISStreamCollector  Low-overhead streaming collector with periodic flush
    QALISConfig           Configuration dataclass
    QALISResult           Per-interaction result dataclass
    QALISBatchResult      Batch evaluation result with summary statistics
    Violation             Threshold violation record
    Alert                 Alert record
"""

from toolkit.collectors.qalis_collector import (
    QALISCollector,
    QALISStreamCollector,
    QALISConfig,
    QALISResult,
    QALISBatchResult,
    Violation,
    Alert,
)

__all__ = [
    "QALISCollector",
    "QALISStreamCollector",
    "QALISConfig",
    "QALISResult",
    "QALISBatchResult",
    "Violation",
    "Alert",
]
