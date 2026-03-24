# QALIS Perturbation Tests

Automated perturbation test suites for the RO (Robustness) dimension.
Covers four test types aligned with RO-1 through RO-4.

## Structure

```
perturbation_tests/
├── README.md                           ← This file
├── typographical/                      ← RO-1 Perturbation Sensitivity
│   ├── typo_perturbation_dataset.csv   ← 5,000 test cases (4 systems × 1,250)
│   ├── typo_summary_statistics.json    ← Per-system and per-type statistics
│   ├── generate_typo_tests.py          ← Regeneration script
│   └── README.md
├── paraphrase/                         ← RO-4 Semantic Invariance
│   ├── paraphrase_invariance_dataset.csv ← 4,000 paraphrase pairs
│   ├── paraphrase_summary_statistics.json
│   ├── generate_paraphrase_tests.py
│   └── README.md
├── ood_detection/                      ← RO-3 OOD Detection
│   ├── ood_detection_dataset.csv       ← 3,000 OOD samples (10 categories)
│   ├── ood_summary_statistics.json
│   ├── generate_ood_tests.py
│   └── README.md
└── prompt_injection/                   ← RO-2 Injection Resistance (SS-3)
    ├── prompt_injection_corpus.csv.gz  ← 2,850 injection attempts (9 categories)
    ├── injection_summary_statistics.json
    ├── attack_pattern_library.json     ← 50 parameterised attack patterns
    ├── generate_injection_tests.py
    └── README.md
```

## Coverage

| Test suite | Metric | n cases | Paper Section |
|------------|--------|---------|---------------|
| Typographical | RO-1 Sensitivity (≤0.10) | 5,000 | Sec 4.3 |
| Paraphrase | RO-4 Invariance (≥0.85) | 4,000 | Sec 4.3 |
| OOD Detection | RO-3 Detection Rate (≥0.80) | 3,000 | Sec 4.3 |
| Prompt Injection | RO-2 Resistance (≥0.97) | 2,850 | Sec 4.3 |

## Configuration

All test parameters are defined in `configs/perturbation_config.yaml`.
Per-system results are stored in `data/perturbation_tests/{system_id}/`.

## Regenerating tests

```bash
# Regenerate all test suites (requires configs/perturbation_config.yaml)
python perturbation_tests/typographical/generate_typo_tests.py
python perturbation_tests/paraphrase/generate_paraphrase_tests.py
python perturbation_tests/ood_detection/generate_ood_tests.py
python perturbation_tests/prompt_injection/generate_injection_tests.py
```
