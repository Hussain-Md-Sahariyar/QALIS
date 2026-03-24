# QALIS Red Team Evaluation

Prompt injection resistance evaluation across all four case systems.
Covers RO-2 (Injection Resistance Rate) and SS-3 (Injection Attack Success Rate).

## Structure

```
red_team/
├── README.md                                    ← This file
├── run_red_team.py                              ← Main runner / analysis script
├── injection_attempts/
│   ├── prompt_injection_corpus.csv.gz           ← 2,850 injection attempts
│   └── README.md                                ← Schema, volume, usage
├── patterns/
│   ├── attack_taxonomy.json                     ← 54 patterns, 9 categories, per-system rates
│   ├── category_summaries.json                  ← Per-category stats and bypass indicators
│   ├── mitigation_register.json                 ← 5 mitigation strategies with effectiveness
│   └── README.md
├── prompts/
│   ├── success_judge_prompt.txt                 ← GPT-4o auto-scorer prompt template
│   ├── category_rubrics.json                    ← Per-category success criteria & edge cases
│   ├── human_review_checklist.md               ← Reviewer guide (10% sample)
│   └── README.md
└── results/
    ├── S1_redteam_summary.json                  ← S1 full by-category results
    ├── S2_redteam_summary.json                  ← S2 full by-category results
    ├── S3_redteam_summary.json                  ← S3 full by-category results
    ├── S4_redteam_summary.json                  ← S4 (clinical threshold ≥0.99)
    ├── red_team_report_2025-01-05.json          ← Aggregate report, key findings
    ├── monthly_resistance_trend.json            ← Oct–Dec 2024 monthly trends
    ├── previous_run_comparison.json             ← Regression check vs Dec 2024 run
    ├── by_category/                             ← Per-category deep dives (9 files)
    │   ├── README.md
    │   ├── encoding_obfuscation_results.json
    │   ├── context_injection_results.json
    │   └── ... (7 more category files)
    └── README.md
```

## Study Summary

| System | Domain | Attempts | Resistance | Threshold | Pass |
|--------|--------|----------|------------|-----------|------|
| S1 | Customer Support (GPT-4o) | 717 | 0.9749 | ≥0.97 | ✓ |
| S2 | AI Code Assistant (Claude 3.5 Sonnet FT) | 719 | 0.9833 | ≥0.97 | ✓ |
| S3 | Document Summarisation (Gemini 1.5 Pro) | 717 | 0.9777 | ≥0.97 | ✓ |
| S4 | Medical Triage (Llama 3.1 70B) | 697 | 0.9928 | ≥0.99 | ✓ |

**Total**: 2,850 attempts · 9 attack categories · 54 patterns · Study period: Oct–Dec 2024

## Attack Categories (hardest → easiest by success rate)

1. `encoding_obfuscation` — hardest (Base64, ROT13, leet speak)
2. `context_injection` — second hardest
3. `emotional_manipulation`
4. `authority_escalation`
5. `role_play_bypass`
6. `direct_instruction_override`
7. `adversarial_few_shot`
8. `prompt_leaking`
9. `chain_of_thought_manipulation` — easiest

## Running the Test Suite

```bash
# Full run (all 4 systems)
python red_team/run_red_team.py

# Single system
python red_team/run_red_team.py --systems S4

# Dry run (no file writes)
python red_team/run_red_team.py --dry-run
```

## Configuration

`configs/red_team_config.yaml` — attack scheduling, weights, thresholds,
auto-scorer model, responsible use policy (IRB: QUATIC-2025-IRB-Annex-B).

## Paper References

- Section 3.3 — Red-team methodology
- Section 4.3 — RO-2 and SS-3 metric definitions and thresholds
- Section 6.2 — RQ2 metric operationalisation results
- Table 3 — RO-2 ≥ 0.97 (S4: ≥ 0.99), SS-3 ≤ 0.02
- Notebook `09_red_team_analysis.ipynb`

## Responsible Use

Attack payloads are stored in obfuscated/parameterised form and are for
internal QA only. See `configs/red_team_config.yaml > responsible_use`.
