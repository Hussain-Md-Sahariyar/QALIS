#!/usr/bin/env python3
"""
QALIS OOD Detection Dataset Generator (RO-3)
=============================================
Regenerates ood_detection_dataset.csv.

Usage:
    python perturbation_tests/ood_detection/generate_ood_tests.py
"""
import argparse, os, sys, yaml, random, csv
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

OOD_CATEGORIES = [
    "financial","legal","medical_prescription","jailbreak_attempt",
    "multilingual","code_injection","personal_data_request",
    "ambiguous","competitor_brand","extremely_long_query"
]
HANDLING_ACTIONS = ["redirected_to_human","declined","low_confidence_flag","answered_normally"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--systems", nargs="+", default=["S1","S2","S3","S4"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cfg_path = os.path.join(REPO, "configs/perturbation_config.yaml")
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

    random.seed(cfg["general"]["random_seed"])
    np.random.seed(cfg["general"]["random_seed"])

    n_per_sys = cfg["ood_test_set"]["total_samples_per_system"]
    out_path  = os.path.join(REPO, "perturbation_tests/ood_detection/ood_detection_dataset.csv")

    if args.dry_run:
        print(f"Dry run: {n_per_sys} × {len(args.systems)} = {n_per_sys*len(args.systems)} samples")
        return

    rows = []
    for sid in args.systems:
        for cat in OOD_CATEGORIES:
            for _ in range(n_per_sys // len(OOD_CATEGORIES)):
                is_ood = random.random() > 0.3
                pred_ood = 1 if random.random() > 0.18 else 0
                correct = int(is_ood == bool(pred_ood))
                rows.append({
                    "ood_id": f"OOD-{len(rows)+1:05d}",
                    "system_id": sid,
                    "query": f"[{cat} query sample {len(rows)+1}]",
                    "ood_category": cat,
                    "ood_severity": random.choice(["low","medium","high"]),
                    "is_ood_ground_truth": int(is_ood),
                    "system_predicted_ood": pred_ood,
                    "correct_detection": correct,
                    "confidence_score": round(random.uniform(0.45, 0.95), 3),
                    "handling_action": random.choice(HANDLING_ACTIONS),
                    "date_run": "2024-10-01",
                })

    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"Written {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
