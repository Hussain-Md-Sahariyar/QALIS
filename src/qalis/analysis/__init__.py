"""
QALIS Analysis Package
======================

Statistical analysis and visualisation utilities used in the empirical
study. Exposes functions for reproducible computation of all key results
reported in the QUATIC 2025 paper.

Submodules:
    rq1      Dimension coverage and independence analysis (RQ1)
    rq2      Metric correlation analysis (RQ2, Figure 4)
    rq3      Comparative effectiveness vs baselines (RQ3, Figure 5)
    stats    Mixed-effects models, Wilcoxon tests, IAA
    figures  Figure generation helpers (Figures 3–6)

Paper reference: §6 (empirical evaluation).
"""

from qalis.analysis.rq1 import dimension_coverage
from qalis.analysis.rq2 import metric_correlations
from qalis.analysis.rq3 import comparative_effectiveness
from qalis.analysis.stats import wilcoxon_comparison, cohen_kappa, descriptive_stats

__all__ = [
    "dimension_coverage",
    "metric_correlations",
    "comparative_effectiveness",
    "wilcoxon_comparison",
    "cohen_kappa",
    "descriptive_stats",
]
