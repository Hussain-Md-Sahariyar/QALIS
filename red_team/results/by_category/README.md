# QALIS Red Team — Results by Category

Per-category deep dives for all 9 attack categories evaluated across S1–S4.

## Schema (each JSON file)

| Field | Description |
|-------|-------------|
| `category` | Machine-readable category name |
| `display_name` | Human-readable name |
| `study_period` | Oct–Dec 2024 |
| `example_payload` | Representative (sanitised) attack payload |
| `primary_mitigations` | List of mitigation strategies applied |
| `per_system` | Per-system stats (attempts, succeeded, resistance rate, threshold pass) |
| `aggregate` | Cross-system totals, mean success rate, hardest/easiest system |
| `paper_reference` | Paper section reference |

## Category Files

| File | Mean Success Rate | Hardest System |
|------|-------------------|----------------|
| `encoding_obfuscation_results.json` | ~2.8% | S1 |
| `context_injection_results.json` | ~2.1% | S1 |
| `role_play_bypass_results.json` | ~1.8% | S2 |
| `direct_instruction_override_results.json` | ~1.7% | S3 |
| `adversarial_few_shot_results.json` | ~1.7% | S3 |
| `emotional_manipulation_results.json` | ~1.4% | S3 |
| `authority_escalation_results.json` | ~1.1% | S3 |
| `prompt_leaking_results.json` | ~1.2% | S3 |
| `chain_of_thought_manipulation_results.json` | ~0.9% | S2 |
