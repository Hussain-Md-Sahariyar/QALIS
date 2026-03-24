"""
BatchCollector — Collect QALIS metrics over a set of interactions.

Useful for offline evaluation of stored query/response datasets, regression
test suites, and CI/CD quality gate checks.

Paper reference: §3.3 (data collection protocol — 3,400 observations).
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from qalis.collectors.collector import CollectorConfig, QALISCollector
from qalis.result import QALISResult

logger = logging.getLogger(__name__)


class BatchCollector:
    """
    Run QALIS metric collection over a batch of interactions.

    Thread-safe: interactions are evaluated in parallel when ``n_workers > 1``.

    Example::

        from qalis.collectors import BatchCollector, CollectorConfig

        cfg = BatchCollector(
            CollectorConfig(system_id="S1", domain="customer_support"),
            n_workers=4,
        )
        interactions = [
            {"query": "...", "response": "...", "context": [...]},
            ...
        ]
        results = batch.collect_all(interactions)
        summary = batch.summary_statistics(results)
    """

    def __init__(self, config: CollectorConfig, n_workers: int = 4) -> None:
        self.config = config
        self.n_workers = n_workers
        # Each worker gets its own collector instance (thread isolation)
        self._collectors = [QALISCollector(config) for _ in range(n_workers)]

    def collect_all(
        self,
        interactions: List[Dict[str, Any]],
        show_progress: bool = False,
    ) -> List[QALISResult]:
        """
        Evaluate QALIS metrics for a list of interactions.

        Args:
            interactions: List of dicts with keys matching QALISCollector.collect()
                          kwargs: ``query``, ``response``, and optionally
                          ``context``, ``reference_answer``, ``latency_ms``, etc.
            show_progress: Log progress every 100 interactions.

        Returns:
            List of QALISResult in the same order as ``interactions``.
        """
        results: List[Optional[QALISResult]] = [None] * len(interactions)

        def _evaluate(idx_item):
            idx, item = idx_item
            worker_idx = idx % self.n_workers
            try:
                r = self._collectors[worker_idx].collect(**item)
                if show_progress and (idx + 1) % 100 == 0:
                    logger.info("BatchCollector: %d / %d evaluated", idx + 1, len(interactions))
                return idx, r
            except Exception as exc:
                logger.error("BatchCollector: error on item %d: %s", idx, exc)
                return idx, None

        with ThreadPoolExecutor(max_workers=self.n_workers) as pool:
            futures = {pool.submit(_evaluate, (i, item)): i
                       for i, item in enumerate(interactions)}
            for future in as_completed(futures):
                idx, result = future.result()
                results[idx] = result

        return [r for r in results if r is not None]

    @staticmethod
    def summary_statistics(results: List[QALISResult]) -> Dict[str, Any]:
        """
        Compute aggregate statistics over a list of QALISResult.

        Returns a dict with:
            - ``mean_composite``
            - ``mean_dimension_scores`` (per dimension)
            - ``violation_rate``         (fraction with any violation)
            - ``pass_rate``              (fraction with composite ≥ 7.0)
            - ``n``                      (number of results)
        """
        if not results:
            return {}

        composites = [r.composite_score for r in results]
        dim_names = list(results[0].dimension_scores.keys())
        dim_means = {
            d: round(
                sum(r.dimension_scores[d].score for r in results if d in r.dimension_scores)
                / len(results),
                3,
            )
            for d in dim_names
        }
        violation_count = sum(1 for r in results if r.threshold_violations)

        return {
            "n": len(results),
            "mean_composite": round(sum(composites) / len(composites), 3),
            "min_composite": round(min(composites), 3),
            "max_composite": round(max(composites), 3),
            "mean_dimension_scores": dim_means,
            "violation_rate": round(violation_count / len(results), 4),
            "pass_rate": round(sum(1 for c in composites if c >= 7.0) / len(results), 4),
        }
