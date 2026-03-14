#!/usr/bin/env python3
import json, os
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_comparison_data():
    return pd.read_csv(f"{BASE}/baselines/comparative_analysis_full.csv")

def wilcoxon_tests(df):
    """Run Wilcoxon signed-rank tests: QALIS vs each baseline per dimension."""
    dims = df["dimension"].unique()
    approaches = [a for a in df["approach"].unique() if a != "QALIS"]
    alpha = 0.01
    n_comparisons = len(dims) * len(approaches)
    bonferroni_alpha = alpha / n_comparisons

    all_sig = True
    for dim in dims:
        qalis_scores = df[(df["dimension"]==dim) & (df["approach"]=="QALIS")]["coverage_score"].values
        for approach in approaches:
            baseline_scores = df[(df["dimension"]==dim) & (df["approach"]==approach)]["coverage_score"].values
            if len(qalis_scores) == len(baseline_scores):
                stat, p = stats.wilcoxon(qalis_scores, baseline_scores, alternative="greater")
                sig = "*" if p < bonferroni_alpha else " "
                print(f"  {dim}: QALIS vs {approach}: W={stat:.1f}, p={p:.5f} {sig}")
                if p >= bonferroni_alpha:
                    all_sig = False
    print(f"\nAll comparisons significant at Bonferroni-corrected alpha: {all_sig}")

def compute_improvement_vs_baselines(df):
    """Compute QALIS improvement margins."""
    summary = df.groupby(["approach","dimension"])["coverage_score"].mean().unstack()
    print("\nMean coverage scores by approach and dimension:")
    print(summary.round(3))

def longitudinal_analysis():
    """Defect detection improvement over 3 months."""
    df = pd.read_csv(f"{BASE}/data/processed/longitudinal/defect_detection_longitudinal.csv")
    print("\nLongitudinal defect detection rates:")
    pivot = df.groupby(["month","approach"])["detection_rate"].mean().unstack()
    print(pivot.round(3))

    # Compute hallucination reduction
    hal = df[(df["defect_category"]=="hallucination_events")]
    qalis_m1 = hal[(hal["approach"]=="QALIS") & (hal["month"]==1)]["detection_rate"].mean()
    qalis_m3 = hal[(hal["approach"]=="QALIS") & (hal["month"]==3)]["detection_rate"].mean()
    undetected_m1 = 1 - qalis_m1
    undetected_m3 = 1 - qalis_m3
    reduction = (undetected_m1 - undetected_m3) / undetected_m1
    print(f"\nHallucination undetected defect reduction: {reduction:.1%}")

def main():
    print("Comparative Effectiveness Analysis\n")
    df = load_comparison_data()
    wilcoxon_tests(df)
    compute_improvement_vs_baselines(df)
    longitudinal_analysis()

if __name__ == "__main__":
    main()
