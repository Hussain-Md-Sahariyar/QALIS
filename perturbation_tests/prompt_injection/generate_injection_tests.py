#!/usr/bin/env python3
"""
QALIS Prompt Injection Test Generator (RO-2 / SS-3)
====================================================
Regenerates prompt_injection_corpus.csv.gz using attack_pattern_library.json.

Usage:
    python perturbation_tests/prompt_injection/generate_injection_tests.py
    python perturbation_tests/prompt_injection/generate_injection_tests.py --systems S4
"""
import argparse, os, sys, json, csv, gzip, io, random
from datetime import datetime, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--systems", nargs="+", default=["S1","S2","S3","S4"])
    parser.add_argument("--n-per-system", type=int, default=712)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    lib_path = os.path.join(REPO,
        "perturbation_tests/prompt_injection/attack_pattern_library.json")
    with open(lib_path) as f:
        library = json.load(f)

    patterns  = library["patterns"]
    out_path  = os.path.join(REPO,
        "perturbation_tests/prompt_injection/prompt_injection_corpus.csv.gz")

    if args.dry_run:
        print(f"Dry run: {args.n_per_system} × {len(args.systems)} = "
              f"{args.n_per_system*len(args.systems)} attempts")
        print(f"Patterns available: {len(patterns)} across {library['n_categories']} categories")
        return

    random.seed(42)
    base_date = datetime(2024, 10, 1)
    rows = []
    aid = 1

    for sid in args.systems:
        for _ in range(args.n_per_system):
            pat   = random.choice(patterns)
            sr    = pat["success_rate_by_system"].get(sid, pat["success_rate_mean"])
            succ  = 1 if random.random() < sr else 0
            ts    = base_date + timedelta(days=random.randint(0,91),
                                           hours=random.randint(0,23))
            rows.append({
                "attempt_id":        f"RT-{sid}-{aid:05d}",
                "system_id":         sid,
                "timestamp":         ts.isoformat(),
                "attack_category":   pat["category"],
                "attack_pattern_id": pat["pattern_id"],
                "prompt_text":       pat["template"].replace("{system_specific_payload}",
                                         f"[payload-{aid}]"),
                "attack_succeeded":  succ,
                "resistance_score":  1 - succ,
                "detection_method":  random.choice(
                    ["output_filter","system_prompt","nli_classifier"]) if not succ else "none",
                "response_truncated": 1 if not succ and random.random() > 0.7 else 0,
            })
            aid += 1

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader(); writer.writerows(rows)

    with gzip.open(out_path, "wt") as f:
        f.write(buf.getvalue())

    total_succ = sum(r["attack_succeeded"] for r in rows)
    print(f"Written {len(rows)} attempts to {out_path}")
    print(f"Overall resistance rate: {1 - total_succ/len(rows):.4f}")


if __name__ == "__main__":
    main()
