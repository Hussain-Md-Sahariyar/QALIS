"""
QALIS Test Suite — Shared Fixtures (conftest.py)
================================================

Provides pytest fixtures shared across all test modules:

    collector_config    CollectorConfig for generic system
    hc_config           CollectorConfig for healthcare domain (S4-like)
    simple_interaction  Minimal interaction dict (query + response)
    rag_interaction     RAG interaction with context chunks
    sample_scores_df    DataFrame of per-system dimension scores (Table 4)
    sample_metrics_raw  Dict of raw metric values for all 24 metrics
"""

import pytest
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# CollectorConfig fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def collector_config():
    """Generic CollectorConfig (no heavy model deps)."""
    from qalis.collectors.collector import CollectorConfig
    return CollectorConfig(
        system_id="TEST-SYS",
        domain="general",
        risk_level="medium",
        layers=[1, 2, 3, 4],
        enable_embeddings=False,   # skip heavy sentence-transformer loading
        enable_audit_trail=False,
        pii_scan=False,
    )


@pytest.fixture
def hc_config():
    """Healthcare CollectorConfig (S4-like, tighter thresholds)."""
    from qalis.collectors.collector import CollectorConfig
    return CollectorConfig(
        system_id="S4-TEST",
        domain="healthcare",
        risk_level="high",
        enable_embeddings=False,
        enable_audit_trail=True,
        pii_scan=True,
    )


# ---------------------------------------------------------------------------
# Interaction fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_interaction():
    """Minimal valid interaction dict."""
    return {
        "query":    "What is your return policy?",
        "response": "Our return window is 30 days from the date of purchase.",
    }


@pytest.fixture
def rag_interaction():
    """RAG-style interaction with context chunks."""
    return {
        "query":    "Summarise the key findings.",
        "response": (
            "The study found that QALIS outperforms all three baseline approaches "
            "across all six quality dimensions. Detection lag improved by 68%."
        ),
        "context": [
            "QALIS was evaluated against ISO 25010, HELM, and MLflow baselines.",
            "All 18 Wilcoxon signed-rank comparisons were significant at α=0.000556.",
            "Mean detection lag: QALIS 1.38h vs baselines 4.43–5.21h.",
        ],
        "reference_answer": (
            "QALIS outperforms baselines on all dimensions with 68% faster detection."
        ),
        "latency_ms": 380.0,
    }


@pytest.fixture
def code_interaction():
    """Code assistant interaction (S2-like)."""
    return {
        "query":    "Fix the null pointer bug in this function.",
        "response": (
            "The bug occurs because `user` can be None. "
            "Add a null check: `if user is None: return None`."
        ),
        "latency_ms": 210.0,
    }


# ---------------------------------------------------------------------------
# Data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_scores_df():
    """
    Per-system dimension scores aligned with Table 4 of the paper.
    Columns: system_id, dimension, mean_score.
    """
    rows = []
    TABLE4 = {
        "S1": {"FC": 7.8, "RO": 6.2, "SF": 8.1, "SS": 7.4, "TI": 5.6, "IQ": 8.3},
        "S2": {"FC": 8.9, "RO": 7.8, "SF": 7.3, "SS": 8.8, "TI": 6.2, "IQ": 7.1},
        "S3": {"FC": 8.2, "RO": 6.8, "SF": 9.1, "SS": 7.9, "TI": 7.5, "IQ": 8.6},
        "S4": {"FC": 7.1, "RO": 8.3, "SF": 8.6, "SS": 9.2, "TI": 8.9, "IQ": 6.8},
    }
    for sid, dims in TABLE4.items():
        for dim, score in dims.items():
            rows.append({"system_id": sid, "dimension": dim, "mean_score": score})
    return pd.DataFrame(rows)


@pytest.fixture
def sample_metrics_raw():
    """
    Representative raw metric values for all 24 QALIS metrics.
    All values are within passing range (no threshold violations).
    """
    return {
        # FC
        "FC-1": 0.87,  # task accuracy
        "FC-2": 0.82,  # context relevance
        "FC-3": 0.85,  # code pass@k
        "FC-4": 0.79,  # annotation accuracy
        # RO
        "RO-1": 0.07,  # perturbation sensitivity (lower=better)
        "RO-2": 0.975, # injection resistance
        "RO-3": 0.83,  # OOD detection rate
        "RO-4": 0.88,  # semantic invariance
        "RO-5": 0.72,  # query specificity
        # SF
        "SF-1": 0.83,  # groundedness
        "SF-2": 0.77,  # attribution coverage
        "SF-3": 1.4,   # hallucination rate per 1K tokens
        # SS
        "SS-1": 0.003, # toxicity rate (lower=better)
        "SS-2": 0.0008,# PII leak rate (lower=better)
        "SS-3": 0.015, # injection success rate (lower=better)
        "SS-4": 0.92,  # refusal precision
        # TI
        "TI-1": 0.74,  # confidence calibration
        "TI-2": 0.68,  # faithfulness rate
        "TI-3": 3.8,   # interpretability score (1–5 Likert)
        "TI-4": 0.96,  # audit completeness
        # IQ
        "IQ-1": 0.997, # availability
        "IQ-2": 420.0, # P95 latency ms
        "IQ-3": 7.2,   # cost efficiency (normalised)
        "IQ-4": 0.92,  # observability coverage
    }


@pytest.fixture
def violation_metrics_raw(sample_metrics_raw):
    """Raw metrics with three threshold violations injected."""
    raw = dict(sample_metrics_raw)
    raw["SF-3"] = 3.5    # hallucination rate > 2.0 → violation
    raw["RO-2"] = 0.955  # injection resistance < 0.97 → violation
    raw["SS-2"] = 0.003  # PII leak rate > 0.001 → violation
    return raw
