# OOD Detection Tests (RO-3)

**3,000 OOD samples** across 4 systems (750 per system), 10 categories.

## Files

| File | Description |
|------|-------------|
| `ood_detection_dataset.csv` | Full dataset — 3,000 rows |
| `ood_summary_statistics.json` | Per-system and per-category statistics |
| `generate_ood_tests.py` | Regeneration script |

## Schema

| Column | Type | Description |
|--------|------|-------------|
| `ood_id` | str | Unique identifier (OOD-NNNNN) |
| `system_id` | str | S1–S4 |
| `query` | str | Input query |
| `ood_category` | str | Category of OOD domain |
| `ood_severity` | str | low / medium / high |
| `is_ood_ground_truth` | int | 1 = out-of-distribution, 0 = in-distribution |
| `system_predicted_ood` | int | System's OOD prediction |
| `correct_detection` | int | 1 if prediction matches ground truth |
| `confidence_score` | float | System's confidence in OOD prediction |
| `handling_action` | str | How system handled OOD query |
| `date_run` | date | Test execution date |

## OOD categories

`financial`, `legal`, `medical_prescription`, `jailbreak_attempt`,
`multilingual`, `code_injection`, `personal_data_request`,
`ambiguous`, `competitor_brand`, `extremely_long_query`

## RO-3 Threshold

**≥ 0.80** correct detection rate overall.
Below-threshold categories (if any) require targeted test expansion.
