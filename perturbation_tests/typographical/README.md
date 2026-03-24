# Typographical Perturbation Tests (RO-1)

**5,000 test cases** across 4 systems (1,250 per system), 7 perturbation types.

## Files

| File | Description |
|------|-------------|
| `typo_perturbation_dataset.csv` | Full dataset — 5,000 rows |
| `typo_summary_statistics.json` | Per-system and per-type statistics |
| `generate_typo_tests.py` | Regeneration script |

## Schema

| Column | Type | Description |
|--------|------|-------------|
| `test_id` | str | Unique identifier (TYPO-NNNNN) |
| `perturbation_type` | str | Always `typographical` |
| `perturbation_subtype` | str | One of 7 types (see below) |
| `original_input` | str | Clean input query |
| `perturbed_input` | str | Perturbed version |
| `perturbation_severity` | float | Normalised edit distance (0–1) |
| `system_id` | str | S1–S4 |
| `clean_output_correctness` | int | FC-1 score on clean input (0/1) |
| `perturbed_output_correctness` | int | FC-1 score on perturbed input (0/1) |
| `sensitivity_score` | float | (clean - perturbed) / clean |
| `semantic_preservation` | float | Cosine similarity of embeddings |
| `date_run` | date | Test execution date |

## Perturbation types

| Subtype | Weight | Description |
|---------|--------|-------------|
| `word_misspelling` | 0.20 | Adjacent character swap within word |
| `character_deletion` | 0.15 | Random non-initial character deleted |
| `character_insertion` | 0.15 | Random adjacent-keyboard insertion |
| `case_variation` | 0.15 | Random case mutations |
| `punctuation_removal` | 0.15 | Punctuation marks removed |
| `word_repetition` | 0.10 | Random word doubled (mobile double-tap) |
| `homophone_substitution` | 0.10 | Common homophone replacement |

## RO-1 Threshold

**≤ 0.10** — sensitivity score must not exceed 10%.
Per-system results: `data/perturbation_tests/{S1..S4}/ro1_sensitivity_summary.json`
