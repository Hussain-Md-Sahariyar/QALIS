import pytest
import pandas as pd
import numpy as np

class TestRQ1:

    def test_dimension(self, sample_scores_df):
        from qalis.analysis.rq1 import dimension_coverage
        results = dimension_coverage(sample_scores_df)
        assert isinstance(results, dict)

    def test_all_dimensions(self, sample_scores_df):
        from qalis.analysis.rq1 import dimension_coverage
        results = dimension_coverage(sample_scores_df)
        assert results["dimensions_active_ge3"] is True

    def test_median(self, sample_scores_df):
        from qalis.analysis.rq1 import dimension_coverage
        results = dimension_coverage(sample_scores_df)
        assert abs(results["median_inter_dim_r"] - 0.31) < 0.10, \
            f"Median |r| = {results['median_inter_dim_r']}"

    def test_lowest(self, sample_scores_df):
        from qalis.analysis.rq1 import dimension_coverage
        results = dimension_coverage(sample_scores_df)
        assert results["lowest_dimension"] == "TI"

    def test_rq1(self, sample_scores_df):
        from qalis.analysis.rq1 import dimension_coverage, check_rq1_assertions
        results = dimension_coverage(sample_scores_df)
        assert check_rq1_assertions(results) is True

    def test_fallback(self):
        from qalis.analysis.rq1 import dimension_coverage
        results = dimension_coverage(None)
        assert "system_profiles" in results
        assert results["lowest_dimension"] == "TI"
        

class TestRQ2:

    def test_correlations(self):
        from qalis.analysis.rq2 import metric_correlations
        results = metric_correlations(None)
        assert isinstance(results, dict)

    def test_correlation_approx(self):
        from qalis.analysis.rq2 import metric_correlations
        results = metric_correlations(None)
        hp = results["highlighted_pairs"]
        r = hp.get("SF-3↔RO-4", hp.get("RO-4↔SF-3"))
        assert r is not None
        assert abs(abs(r) - 0.61) < 0.05, f"|SF-3↔RO-4| = {abs(r)}, expected ~0.61"

    def test_cross_dimension(self):
        from qalis.analysis.rq2 import metric_correlations
        results = metric_correlations(None)
        assert len(results["cross_dimension_pairs"]) > 0

    def test_rq2_assertions(self):
        from qalis.analysis.rq2 import metric_correlations, check_rq2_assertions
        results = metric_correlations(None)
        assert check_rq2_assertions(results) is True


class TestRQ3:

    def test_effectiveness(self):
        from qalis.analysis.rq3 import comparative_effectiveness
        results = comparative_effectiveness(None)
        assert isinstance(results, dict)

    def test_wilcoxon(self):
        from qalis.analysis.rq3 import comparative_effectiveness
        results = comparative_effectiveness(None)
        assert results["all_significant"] is True

    def test_wilcoxon_comparisons(self):
        from qalis.analysis.rq3 import comparative_effectiveness
        results = comparative_effectiveness(None)
        assert len(results["wilcoxon_results"]) == 18

    def test_detection(self):
        from qalis.analysis.rq3 import comparative_effectiveness
        results = comparative_effectiveness(None)
        assert results["detection_improvement_pct"] >= 60.0

    def test_outperforms(self):
        from qalis.analysis.rq3 import comparative_effectiveness, _EFFECTIVENESS
        results = comparative_effectiveness(None)
        for row in results["wilcoxon_results"]:
            assert row["delta"] > 0, \
                f"QALIS outperform {row['baseline']} on {row['dimension']}"

    def test_assertions_pass(self):
        from qalis.analysis.rq3 import comparative_effectiveness, check_rq3_assertions
        results = comparative_effectiveness(None)
        assert check_rq3_assertions(results) is True


class TestStats:

    def test_agreement(self):
        from qalis.analysis.stats import cohen_kappa
        a = [1, 0, 1, 1, 0, 0, 1, 0]
        assert cohen_kappa(a, a) == pytest.approx(1.0, abs=0.001)

    def test_value(self):
        from qalis.analysis.stats import cohen_kappa
        a = [1]*70 + [0]*8 + [1]*4 + [0]*3  # synthetic, majority agreement
        b = [1]*72 + [0]*7 + [1]*2 + [0]*4
        k = cohen_kappa(a[:len(b)], b)
        assert -1.0 <= k <= 1.0

    def test_keys(self):
        from qalis.analysis.stats import descriptive_stats
        vals = [7.1, 7.5, 8.0, 8.2, 7.8]
        stats = descriptive_stats(vals)
        for key in ["n", "mean", "std", "median", "min", "max"]:
            assert key in stats

    def test_values(self):
        from qalis.analysis.stats import descriptive_stats
        stats = descriptive_stats([1.0, 2.0, 3.0, 4.0, 5.0])
        assert stats["mean"] == pytest.approx(3.0, abs=0.001)
        assert stats["n"] == 5

    def test_empty(self):
        from qalis.analysis.stats import descriptive_stats
        stats = descriptive_stats([])
        assert stats["n"] == 0

    def test_comparison(self):
        from qalis.analysis.stats import wilcoxon_comparison
        import numpy as np
        rng = np.random.default_rng(42)
        x = rng.normal(loc=8.0, scale=0.5, size=50)
        y = rng.normal(loc=6.5, scale=0.5, size=50)
        stat, p = wilcoxon_comparison(x, y, alternative="greater")
        assert p < 0.01, f"Expected significant difference, got p={p:.4f}"

    def test_trend(self):
        from qalis.analysis.stats import mixed_effects_trend
        df = pd.DataFrame({
            "month": [1, 2, 3, 1, 2, 3],
            "approach": ["QALIS"] * 3 + ["baseline"] * 3,
            "detection_rate": [0.75, 0.80, 0.85, 0.60, 0.60, 0.61],
        })
        result = mixed_effects_trend(df)
        assert len(result) == 2
        qalis_row = result[result["group"] == "QALIS"].iloc[0]
        baseline_row = result[result["group"] == "baseline"].iloc[0]
        assert qalis_row["slope"] > baseline_row["slope"]
