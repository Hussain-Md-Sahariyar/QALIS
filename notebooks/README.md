# QALIS Notebooks

Jupyter notebooks for exploration, analysis, and paper replication.

## Setup

```bash
pip install jupyter matplotlib seaborn scipy pandas numpy
cd QALIS
jupyter notebook notebooks/
```

## Notebooks

| # | Notebook | Description | Paper ref |
|---|----------|-------------|-----------|
| 01 | `01_getting_started.ipynb` | Framework overview, radar chart, Table 4 | Sec 4, Fig 3 |
| 02 | `02_metric_correlations.ipynb` | Correlation heatmap, RQ1 independence check | Sec 6.2, Fig 4 |
| 03 | `03_longitudinal_analysis.ipynb` | Longitudinal detection trends, detection lag | Sec 6.3, Fig 6 |
| 04 | `04_baseline_comparison.ipynb` | QALIS vs baselines bar chart, Wilcoxon tests | Sec 6.3, Fig 5 |
| 05 | `05_annotation_analysis.ipynb` | FC-4, TI-2, TI-3 annotation datasets; IAA | Sec 3.4, 6.1 |
| 06 | `06_perturbation_analysis.ipynb` | RO-1 typo tests, RO-3 OOD, RO-4 invariance | Sec 4.3, 6.2 |
| 07 | `07_full_replication.ipynb` | **One-stop replication of all 17 key paper results** | All |
| 08 | `08_incident_analysis.ipynb` | 42 incidents: QALIS lag vs baseline, MTTR | Sec 6.3 |
| 09 | `09_red_team_analysis.ipynb` | 2,850 injection attempts, RO-2 / SS-3 | Sec 4.3, 6.2 |
| 10 | `10_system_profiles.ipynb` | Per-system deep dives (S1–S4) | Sec 5, 6.1 |
| 11 | `11_interview_analysis.ipynb` | Thematic analysis, 8 themes, IAA k=0.81 | Sec 5 |
| 12 | `12_threshold_calibration.ipynb` | Threshold sweeps, domain overrides, weight sensitivity | Sec 3.3 |
| 13 | `13_statistical_models.ipynb` | Mixed-effects models, Wilcoxon, kappa, descriptive stats | Sec 3.5 |
| 14 | `14_baseline_deep_dive.ipynb` | ISO 25010 / HELM / MLflow methodology and blind spots | Sec 4.4 |

## Recommended order

1. **New to the repo?** Start with `01_getting_started.ipynb`
2. **Verifying results?** Run `07_full_replication.ipynb` — checks all 17 key numbers
3. **Exploring a specific topic?** Use the paper reference column above to find the right notebook

## Expected figure outputs

Saved to `docs/figures/` by notebooks 01-04:
- `figure3_radar_quality_profiles.png`
- `figure4_correlation_heatmap.png`
- `figure5_comparative_effectiveness.png`
- `figure6_longitudinal_detection.png`
