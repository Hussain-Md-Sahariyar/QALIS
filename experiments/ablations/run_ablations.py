#!/usr/bin/env python3
import os, json, sys
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

DIMS = ["FC", "RO", "SF", "SS", "TI", "IQ"]

def load_scores():
    path = os.path.join(REPO, "data/processed/aggregated/qalis_master_scores.csv")
    return pd.read_csv(path)


def run_dimension_dropout(df):
    """exp_abl_001: Assess impact of removing each dimension on composite validity."""
    print("\nexp_abl_001: Dimension Dropout Ablation")

    # Full composite per system
    pivot = df.pivot_table(index="system_id", columns="dimension", values="mean_score")
    full_composite = pivot.mean(axis=1).mean()
    print(f"Full composite (all dims): {full_composite:.3f}")

    for dim in DIMS:
        remaining = [d for d in DIMS if d in pivot.columns and d != dim]
        if not remaining:
            continue
        reduced = pivot[remaining].mean(axis=1).mean()
        delta = reduced - full_composite
        print(f"Exclude {dim}: composite={reduced:.3f}  delta={delta:+.3f}")

    stored = json.load(open(os.path.join(REPO,
        "experiments/ablations/exp_abl_001_dimension_dropout.json")))
    print(f"\nStored result - full detection rate: {stored['results']['full_qalis_incident_detection_rate']}")
    print(f"Stored result - most impactful excluded dim: {stored['results']['most_impactful_dimension']}")


def run_weight_sensitivity(df):
    """exp_abl_003: Composite score stability across weight schemes."""
    print("\nexp_abl_003: Weight Sensitivity Ablation")

    pivot = df.pivot_table(index="system_id", columns="dimension", values="mean_score")

    weight_schemes = {
        "equal":             {d: 1.0 for d in DIMS},
        "safety_heavy":      {{d: 1.0 for d in DIMS}, "SS": 2.0},
        "faithfulness_heavy":{{d: 1.0 for d in DIMS}, "SF": 2.0},
        "integration_heavy": {{d: 1.0 for d in DIMS}, "IQ": 2.0},
        "transparency_heavy":{{d: 1.0 for d in DIMS}, "TI": 2.0},
    }

    rankings = {}
    for scheme_name, weights in weight_schemes.items():
        available = {d: w for d, w in weights.items() if d in pivot.columns}
        total_weight = sum(available.values())
        composite = {
            sys_id: sum(pivot.loc[sys_id, d] * w for d, w in available.items()
                        if d in pivot.columns) / total_weight
            for sys_id in pivot.index
        }
        ranking = sorted(composite, key=composite.get, reverse=True)
        rankings[scheme_name] = ranking
        scores_str = " | ".join(f"{s}={composite[s]:.2f}" for s in ranking)
        print(f"  {scheme_name:<22}: {' > '.join(ranking)}  ({scores_str})")

    # Rank correlation with equal-weight default
    from scipy.stats import spearmanr
    default_rank = rankings["equal"]
    for scheme, rank in rankings.items():
        if scheme == "equal":
            continue
        r, _ = spearmanr(
            [default_rank.index(s) for s in default_rank],
            [rank.index(s) for s in default_rank]
        )
        print(f"  Spearman r vs equal ({scheme}): {r:.3f}")


def main():
    print("=" * 60)
    print("QALIS Ablation Study Runner")
    print("=" * 60)

    df = load_scores()
    run_dimension_dropout(df)
    run_weight_sensitivity(df)

    print("\n" + "=" * 60)
    print("=" * 60)


if __name__ == "__main__":
    main()
