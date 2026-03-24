# QALIS Red Team — Attack Patterns

Parameterised attack pattern library for prompt injection resistance testing.

## Files

| File | Description |
|------|-------------|
| `attack_taxonomy.json` | 54 patterns across 9 categories with per-system success rates |
| `category_summaries.json` | Per-category statistics, bypass indicators, mitigation strategies |
| `mitigation_register.json` | 5 active mitigations with effectiveness scores |

## Attack Taxonomy Structure

Each pattern in `attack_taxonomy.json` includes:
- `pattern_id` — unique identifier (PAT-NNN)
- `category` — one of 9 attack categories
- `severity` — low / medium / high
- `success_rate_mean` — mean across all 4 systems
- `success_rate_by_system` — per-system breakdown
- `mitigated_by` — primary mitigation strategy applied
- `first_observed` — date added to corpus

## Categories by Mean Success Rate

| Category | Mean Rate | Severity | Primary Mitigation |
|----------|-----------|----------|-------------------|
| `encoding_obfuscation` | 2.8% | High | encoding_detection + output_filter |
| `context_injection` | 2.1% | High | context_isolation |
| `role_play_bypass` | 1.8% | Medium | system_prompt_hardening |
| `direct_instruction_override` | 1.7% | High | system_prompt_hardening |
| `adversarial_few_shot` | 1.7% | Medium | few_shot_sanitisation |
| `emotional_manipulation` | 1.4% | Low | system_prompt_hardening |
| `authority_escalation` | 1.1% | Medium | system_prompt_hardening |
| `prompt_leaking` | 1.2% | Medium | system_prompt_protection |
| `chain_of_thought_manipulation` | 0.9% | Low | system_prompt_hardening |

## Adding Patterns

New patterns should be added to `attack_taxonomy.json` and the canonical copy
at `perturbation_tests/prompt_injection/attack_pattern_library.json` should be
updated in parallel.

Pattern naming: `PAT-NNN` where NNN increments from the current maximum.
