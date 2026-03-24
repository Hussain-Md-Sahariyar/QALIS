#!/usr/bin/env python3
import os, json, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXP_DIR = os.path.join(REPO, "experiments/threshold_sensitivity")


def print_sweep(exp_file, metric_id):
    path = os.path.join(EXP_DIR, exp_file)
    exp = json.load(open(path))

    print(f"\n{'='*60}")
    print(f"  {exp['name']}")
    print(f"  Default threshold: {exp['default_threshold']}  Direction: {exp['direction']}")
    print(f"{'='*60}")
    print(f"  {'Threshold':>10} {'FPR':>8} {'FNR':>8} {'Precision':>10} {'Recall':>8} {'F1':>8} {'Default':>8}")
    print(f"  {'-'*62}")

    for r in exp["sweep_results"]:
        marker = " ←" if r.get("is_default") else ""
        print(f"  {str(r['threshold']):>10} {r['false_positive_rate']:>8.3f} "
              f"{r['false_negative_rate']:>8.3f} {r['alert_precision']:>10.3f} "
              f"{r['alert_recall']:>8.3f} {r['f1']:>8.3f}{marker}")

    print(f"\n  Optimal threshold by F1: {exp['optimal_threshold_by_f1']}")
    print(f"  Recommendation: {exp['recommendation']}")


def print_domain_overrides():
    path = os.path.join(EXP_DIR, "exp_thr_003_domain_override_impact.json")
    exp = json.load(open(path))

    print(f"\n{'='*60}")
    print(f"  {exp['name']}")
    print(f"{'='*60}")

    for o in exp["domain_overrides_tested"]:
        print(f"\n  {o['system']} / {o['metric']}: {o['default_thresh']} → {o['domain_thresh']}")
        print(f"    Extra violations/month: {o['additional_violations_per_month']}")
        print(f"    FPR change:  {o['false_positive_rate_change']:+.3f}")
        print(f"    Verdict:     {o['verdict']}")

    print(f"\n  Conclusion: {exp['conclusion']}")


def main():
    print("\n" + "=" * 60)
    print("  QALIS Threshold Sensitivity Analysis")
    print("=" * 60)

    print_sweep("exp_thr_001_sf3_threshold_sweep.json", "SF-3")
    print_sweep("exp_thr_002_ro2_threshold_sweep.json", "RO-2")
    print_domain_overrides()

    print("\n" + "=" * 60)
    print("  Threshold sensitivity analysis complete.")
    print("  See experiments/threshold_sensitivity/ for full JSON results.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
