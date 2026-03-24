"""
QALIS Statistical Helpers
=========================

Utility functions for the mixed-effects models, inter-annotator reliability,
and descriptive statistics reported in §3.5 and §6 of the paper.

Key functions:
    wilcoxon_comparison    One-sided Wilcoxon signed-rank test
    cohen_kappa            Cohen's κ for two annotators
    fleiss_kappa           Fleiss' κ for ≥ 3 annotators
    cronbach_alpha         Cronbach's α for scale reliability
    descriptive_stats      Mean, SD, min/max for a metric column
    mixed_effects_trend    OLS slope as proxy for LME longitudinal trend
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple
import math
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon as _scipy_wilcoxon, pearsonr, kendalltau


# ---------------------------------------------------------------------------
# Wilcoxon signed-rank test
# ---------------------------------------------------------------------------

def wilcoxon_comparison(
    x: Sequence[float],
    y: Sequence[float],
    alternative: str = "greater",
) -> Tuple[float, float]:
    """
    One-sided Wilcoxon signed-rank test: H₁: x > y.

    Args:
        x:           Observations for approach A (QALIS).
        y:           Observations for approach B (baseline).
        alternative: 'greater' | 'less' | 'two-sided'.

    Returns:
        (W statistic, p-value)
    """
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    stat, p = _scipy_wilcoxon(x_arr, y_arr, alternative=alternative)
    return float(stat), float(p)


# ---------------------------------------------------------------------------
# Inter-annotator reliability
# ---------------------------------------------------------------------------

def cohen_kappa(
    rater_a: Sequence[Any],
    rater_b: Sequence[Any],
) -> float:
    """
    Compute Cohen's κ for two raters with nominal categories.

    Args:
        rater_a: Labels from rater A.
        rater_b: Labels from rater B.

    Returns:
        Cohen's κ (float in [-1, 1]).
    """
    a = list(rater_a)
    b = list(rater_b)
    assert len(a) == len(b), "Both raters must have the same number of annotations."
    categories = sorted(set(a) | set(b))
    n = len(a)
    # Observed agreement
    p_o = sum(1 for ai, bi in zip(a, b) if ai == bi) / n
    # Expected agreement
    p_e = sum(
        (a.count(cat) / n) * (b.count(cat) / n) for cat in categories
    )
    if p_e == 1.0:
        return 1.0
    return round((p_o - p_e) / (1.0 - p_e), 4)


def fleiss_kappa(ratings: np.ndarray) -> float:
    """
    Compute Fleiss' κ for ≥ 3 raters.

    Args:
        ratings: 2D numpy array of shape (n_items, n_categories),
                 where each cell is the count of raters assigning
                 that category to that item.

    Returns:
        Fleiss' κ (float).
    """
    ratings = np.asarray(ratings, dtype=float)
    n_items, n_cats = ratings.shape
    n_raters = ratings[0].sum()

    p_j = ratings.sum(axis=0) / (n_items * n_raters)   # marginal proportions
    P_e = float((p_j ** 2).sum())

    P_i = ((ratings ** 2).sum(axis=1) - n_raters) / (n_raters * (n_raters - 1))
    P_bar = float(P_i.mean())

    if P_e == 1.0:
        return 1.0
    return round((P_bar - P_e) / (1.0 - P_e), 4)


def cronbach_alpha(item_scores: np.ndarray) -> float:
    """
    Compute Cronbach's α for a set of scale items.

    Args:
        item_scores: 2D array (n_respondents × n_items).

    Returns:
        Cronbach's α (float).
    """
    items = np.asarray(item_scores, dtype=float)
    n_items = items.shape[1]
    item_variances = items.var(axis=0, ddof=1)
    total_variance = items.sum(axis=1).var(ddof=1)
    if total_variance == 0:
        return 0.0
    return round(
        (n_items / (n_items - 1)) * (1 - item_variances.sum() / total_variance),
        4,
    )


# ---------------------------------------------------------------------------
# Descriptive statistics
# ---------------------------------------------------------------------------

def descriptive_stats(values: Sequence[float]) -> Dict[str, float]:
    """
    Return a dict with mean, std, median, min, max, and n.

    Args:
        values: Sequence of numeric observations.

    Returns:
        Dict with keys: n, mean, std, median, min, max.
    """
    arr = np.asarray(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0:
        return {"n": 0, "mean": float("nan"), "std": float("nan"),
                "median": float("nan"), "min": float("nan"), "max": float("nan")}
    return {
        "n":      int(len(arr)),
        "mean":   round(float(arr.mean()), 4),
        "std":    round(float(arr.std(ddof=1)), 4),
        "median": round(float(np.median(arr)), 4),
        "min":    round(float(arr.min()), 4),
        "max":    round(float(arr.max()), 4),
    }


# ---------------------------------------------------------------------------
# Longitudinal trend (OLS proxy for LME)
# ---------------------------------------------------------------------------

def mixed_effects_trend(
    longitudinal_df: pd.DataFrame,
    outcome_col: str = "detection_rate",
    time_col: str = "month",
    group_col: str = "approach",
) -> pd.DataFrame:
    """
    Estimate linear trend (slope) per group as a proxy for LME analysis.

    Args:
        longitudinal_df: DataFrame with at least [time_col, outcome_col, group_col].
        outcome_col:     Column to regress (default: 'detection_rate').
        time_col:        Time variable (default: 'month').
        group_col:       Group variable (default: 'approach').

    Returns:
        DataFrame with columns [group, slope, intercept, r2, p].
        Positive slope = improving trend over time.
    """
    from scipy.stats import linregress
    results = []
    for group, sub in longitudinal_df.groupby(group_col):
        monthly = sub.groupby(time_col)[outcome_col].mean()
        x = monthly.index.astype(float).values
        y = monthly.values
        if len(x) < 2:
            continue
        slope, intercept, r, p, _ = linregress(x, y)
        results.append({
            "group":     group,
            "slope":     round(float(slope), 5),
            "intercept": round(float(intercept), 4),
            "r2":        round(float(r ** 2), 4),
            "p":         round(float(p), 5),
        })
    return pd.DataFrame(results)
