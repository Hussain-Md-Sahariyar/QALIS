# QALIS Red Team — Results

All red-team evaluation outputs for the study period (Oct–Dec 2024).

## Files

| File | Description |
|------|-------------|
| `S1_redteam_summary.json` | S1 full results by category (GPT-4o) |
| `S2_redteam_summary.json` | S2 full results by category (Claude 3.5 Sonnet FT) |
| `S3_redteam_summary.json` | S3 full results by category (Gemini 1.5 Pro) |
| `S4_redteam_summary.json` | S4 full results, clinical threshold ≥0.99 (Llama 3.1 70B) |
| `red_team_report_2025-01-05.json` | Aggregate report with key findings and recommendations |
| `latest_run_summary.json` | Alias to most recent full run (for CI/CD pipeline) |
| `monthly_resistance_trend.json` | Oct–Dec per-system monthly breakdowns |
| `previous_run_comparison.json` | Regression check vs Dec 2024 run |
| `ci_mini_red_team_suite.json` | 100-case CI/CD mini suite (≤3 min, 3 categories) |
| `by_category/` | Per-category deep dives (9 files) |

## Summary Table

| System | Attempts | Succeeded | Resistance | Threshold | Pass |
|--------|----------|-----------|------------|-----------|------|
| S1 — Customer Support | 717 | 18 | 0.9749 | ≥0.97 | ✓ |
| S2 — AI Code Assistant | 719 | 12 | 0.9833 | ≥0.97 | ✓ |
| S3 — Document Summarisation | 717 | 16 | 0.9777 | ≥0.97 | ✓ |
| S4 — Medical Triage | 697 | 5 | 0.9928 | ≥0.99 | ✓ |

## `by_category/` contents

One JSON file per attack category — each contains aggregate stats,
per-system breakdown, example payload, and primary mitigations applied.

| File | Category |
|------|----------|
| `encoding_obfuscation_results.json` | Base64 / ROT13 / leet speak |
| `context_injection_results.json` | Payload embedded in context |
| `role_play_bypass_results.json` | DAN / persona bypass |
| `direct_instruction_override_results.json` | SYSTEM/ADMIN commands |
| `adversarial_few_shot_results.json` | Compliance examples + request |
| `emotional_manipulation_results.json` | Urgency / distress framing |
| `authority_escalation_results.json` | Developer / admin impersonation |
| `prompt_leaking_results.json` | System prompt extraction |
| `chain_of_thought_manipulation_results.json` | Reasoning-path hijack |
