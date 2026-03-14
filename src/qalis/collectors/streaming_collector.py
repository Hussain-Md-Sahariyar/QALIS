"""
StreamingCollector — Low-latency collector for streaming LLM responses.

For systems where the response arrives token-by-token (e.g. IDE plugin S2),
this collector accumulates the response stream and defers metric computation
to stream completion, while tracking token-level IQ-2 latency buckets.

Paper reference: §4.4 — IQ-3 exclusion rationale for S2 streaming FIM.
"""

import logging
import time
from typing import Any, Dict, Generator, List, Optional

from qalis.collectors.collector import CollectorConfig, QALISCollector
from qalis.result import QALISResult

logger = logging.getLogger(__name__)


class StreamingCollector:
    """
    Wraps a streaming LLM response and collects QALIS metrics on completion.

    Usage::

        collector = StreamingCollector(
            CollectorConfig(system_id="S2", domain="code_generation")
        )
        with collector.stream_context(query=query) as ctx:
            for token in llm.stream(query):
                ctx.push_token(token)
        result = ctx.result()
    """

    def __init__(self, config: CollectorConfig) -> None:
        self.config = config
        self._inner = QALISCollector(config)

    class _StreamContext:
        def __init__(self, collector: "StreamingCollector", query: str,
                     context: Optional[List[str]] = None) -> None:
            self._collector = collector
            self._query = query
            self._context = context or []
            self._tokens: List[str] = []
            self._t0: float = 0.0
            self._t_first_token: Optional[float] = None
            self._t_end: Optional[float] = None
            self._result: Optional[QALISResult] = None

        def __enter__(self):
            self._t0 = time.perf_counter()
            return self

        def push_token(self, token: str) -> None:
            if self._t_first_token is None:
                self._t_first_token = time.perf_counter()
            self._tokens.append(token)

        def __exit__(self, *args):
            self._t_end = time.perf_counter()
            response = "".join(self._tokens)
            latency_ms = (self._t_end - self._t0) * 1000.0
            self._result = self._collector._inner.collect(
                query=self._query,
                response=response,
                context=self._context,
                latency_ms=latency_ms,
            )

        def result(self) -> Optional[QALISResult]:
            return self._result

        @property
        def ttft_ms(self) -> Optional[float]:
            """Time-to-first-token in milliseconds."""
            if self._t_first_token is None:
                return None
            return (self._t_first_token - self._t0) * 1000.0

    def stream_context(
        self, query: str, context: Optional[List[str]] = None
    ) -> "_StreamContext":
        return self._StreamContext(self, query, context)
