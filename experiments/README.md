# QALIS Experiments

This directory contains all experiment tracking records, ablation studies, and
sensitivity analyses conducted during the QALIS study (QUATIC 2025).

## Structure

```
experiments/
├── README.md                          ← This file
├── experiment_registry.json           ← Master index of all experiments
├── rq1_dimension_coverage/            ← RQ1: Do 6 dimensions capture distinct quality?
│   ├── exp_rq1_001_independence_test.json
│   ├── exp_rq1_002_dimension_activation.json
│   └── rq1_results_summary.md
├── rq2_metric_operationalization/     ← RQ2: Can metrics be reliably collected?
│   ├── exp_rq2_001_collection_completeness.json
│   ├── exp_rq2_002_nli_model_comparison.json
│   ├── exp_rq2_003_embedding_model_comparison.json
│   └── rq2_results_summary.md
├── rq3_comparative_effectiveness/     ← RQ3: Is QALIS more effective than baselines?
│   ├── exp_rq3_001_wilcoxon_tests.json
│   ├── exp_rq3_002_longitudinal_trend.json
│   ├── exp_rq3_003_detection_lag_analysis.json
│   └── rq3_results_summary.md
├── ablations/                         ← Metric subset and weight ablations
│   ├── exp_abl_001_dimension_dropout.json
│   ├── exp_abl_002_metric_subset_fc.json
│   ├── exp_abl_003_weight_sensitivity.json
│   └── ablation_summary.md
└── threshold_sensitivity/             ← Threshold calibration sensitivity
    ├── exp_thr_001_sf3_threshold_sweep.json
    ├── exp_thr_002_ro2_threshold_sweep.json
    ├── exp_thr_003_domain_override_impact.json
    └── threshold_sensitivity_summary.md
```

## Experiment Naming Convention

`exp_{category}_{number}_{short_description}.json`

Categories: `rq1`, `rq2`, `rq3`, `abl` (ablation), `thr` (threshold)

## Running Experiments

```bash
# Reproduce all RQ experiments
python analysis/rq1/dimension_coverage_analysis.py
python analysis/rq2/metric_correlation_analysis.py
python analysis/rq3/comparative_effectiveness_analysis.py

# Reproduce ablation studies
python experiments/ablations/run_ablations.py

# Reproduce threshold sensitivity analysis
python experiments/threshold_sensitivity/run_threshold_sweep.py
```

## Key Findings Cross-Reference

| Finding | Experiment | Paper Section |
|---------|-----------|---------------|
| Median inter-dimension \|r\| = 0.31 | exp_rq1_001 | Section 6.1 |
| All 6 dimensions active in ≥3 systems | exp_rq1_002 | Section 6.1 |
| 97.3% metric collection completeness | exp_rq2_001 | Section 6.2 |
| SF-3 ↔ RO-4 r = 0.61 | exp_rq2_001 | Section 6.2 / Figure 4 |
| IQ-2 ↔ IQ-1 r = 0.74 | exp_rq2_001 | Section 6.2 / Figure 4 |
| All RQ3 Wilcoxon tests p < 0.001 | exp_rq3_001 | Section 6.3 |
| 81% hallucination reduction by M3 | exp_rq3_002 | Section 6.3 / Figure 6 |
| 68% earlier detection on average | exp_rq3_003 | Section 6.3 |
