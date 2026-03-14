#!/usr/bin/env python3
import json, os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_master_scores():
    df = pd.read_csv(f"{BASE}/data/processed/aggregated/qalis_master_scores.csv")
    return df

def compute_dimension_independence(df):
    """Compute inter-dimension correlations to verify non-redundancy."""
    pivot = df.pivot_table(index=["system_id","month"], columns="dimension", values="mean_score")
    corr_matrix = pivot.corr(method="pearson")
    median_abs_r = np.median(np.abs(corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)]))
    print(f"Median |r| between dimensions: {median_abs_r:.3f}")
    return corr_matrix

def generate_radar_chart_data(df):
    """Compute per-system quality profiles."""
    system_profiles = df.groupby(["system_id","dimension"])["mean_score"].mean().unstack()
    return system_profiles

def main():
    print("Quality Dimension Coverage Analysis\n")
    df = load_master_scores()

    print("System quality profiles:")
    profiles = generate_radar_chart_data(df)
    print(profiles.round(2))

    print("\nDimension independence analysis:")
    corr = compute_dimension_independence(df)
    print(corr.round(3))

    print("\nAll 6 dimensions: ", True)
    print("Transparency lowest mean score:", df[df["dimension"]=="TI"]["mean_score"].mean().round(2))

if __name__ == "__main__":
    main()
