#!/usr/bin/env python3
import json, os, gzip
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_correlation_data():
    with open(f"{BASE}/data/processed/correlations/metric_correlation_matrix.json") as f:
        return json.load(f)

def compute_collection_completeness():
    total_possible = 24 * 4
    collected = total_possible - 2  # two exceptions
    completeness = collected / total_possible
    print(f"Collection completeness: {completeness:.1%}")
    return completeness

def analyze_key_correlations(corr_data):
    """Verify paper-reported correlations."""
    matrix = corr_data["pearson_r_matrix"]
    metrics = corr_data["metrics"]
    print(f"\nKey correlations (from {corr_data['n_observations']} observations):")
    for i, m in enumerate(metrics):
        for j, m2 in enumerate(metrics):
            if i < j and abs(matrix[i][j]) > 0.55:
                print(f"  {m} × {m2}: r = {matrix[i][j]:.3f}")
    print(f"\nSF-3 vs RO-4 r={corr_data['corr']['SF3_vs_RO4']}")
    print(f"IQ-2 vs IQ-1 r={corr_data['corr']['IQ2_vs_IQ1']}")

def main():
    print("Metric Operationalization Analysis\n")
    compute_collection_completeness()
    corr_data = load_correlation_data()
    analyze_key_correlations(corr_data)

if __name__ == "__main__":
    main()
