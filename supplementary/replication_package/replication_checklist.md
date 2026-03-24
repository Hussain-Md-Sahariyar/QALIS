# Replication Checklist

Step-by-step verification guide for the QALIS replication package.
Cross-check each result against the expected values from the paper.

---

## Setup

- [ ] Clone the repository
- [ ] Create conda environment: `conda env create -f supplementary/replication_package/environment.yml`
- [ ] Activate environment: `conda activate qalis-replication`
- [ ] Install package: `pip install -e .` (from repository root)
- [ ] Run full replication: `python supplementary/replication_package/replicate_all_results.py --verify`

---

## RQ1 — Quality Dimension Coverage (§6.1, Table 4, Figure 3)

Run: `python supplementary/replication_package/replicate_all_results.py --target rq1 --verify`

| Check | Expected value | Tolerance | Pass? |
|-------|----------------|-----------|-------|
| S1 composite score | 7.23 | ± 0.15 | ☐ |
| S2 composite score | 7.68 | ± 0.15 | ☐ |
| S3 composite score | 8.02 | ± 0.15 | ☐ |
| S4 composite score | 8.15 | ± 0.15 | ☐ |
| Overall mean composite | 7.77 | ± 0.10 | ☐ |
| Median inter-dimension \|r\| | 0.31 | ± 0.08 | ☐ |
| Lowest-scoring dimension | TI | exact | ☐ |
| All 6 dimensions active in ≥ 3 systems | True | exact | ☐ |
| TI mean score across systems | 7.05 | ± 0.30 | ☐ |
| TI standard deviation | 1.35 | ± 0.30 | ☐ |

**Figure 3** (radar chart):
- [ ] Four system profiles plotted (S1–S4)
- [ ] S4 has highest SS spoke; S1 has lowest TI spoke
- [ ] File written to `analysis/figures/figure3_radar_chart.pdf`

---

## RQ2 — Metric Correlations (§6.2, Figure 4)

Run: `python supplementary/replication_package/replicate_all_results.py --target rq2 --verify`

| Check | Expected value | Tolerance | Pass? |
|-------|----------------|-----------|-------|
| Pearson r: SF-3 ↔ RO-4 | −0.61 | ± 0.05 | ☐ |
| Pearson r: IQ-2 ↔ IQ-1 | −0.74 | ± 0.05 | ☐ |
| Pearson r: SF-1 ↔ SF-3 | −0.52 | ± 0.08 | ☐ |
| Pearson r: SS-1 ↔ SS-2 | +0.38 | ± 0.08 | ☐ |
| All 24 metrics collected in ≥ 3 systems | True | exact | ☐ |

**Figure 4** (correlation heatmap):
- [ ] 8 × 8 heatmap for key metrics
- [ ] Negative cross-dimension correlations annotated
- [ ] File written to `analysis/figures/figure4_correlation_heatmap.pdf`

---

## RQ3 — Comparative Effectiveness (§6.3, Table 5, Figures 5–6)

Run: `python supplementary/replication_package/replicate_all_results.py --target rq3 --verify`

| Check | Expected value | Tolerance | Pass? |
|-------|----------------|-----------|-------|
| Wilcoxon comparisons (total) | 18 | exact | ☐ |
| Wilcoxon significant at Bonferroni α = 0.000556 | 18 / 18 | exact | ☐ |
| QALIS vs ISO25010 mean advantage | ≥ +0.20 (all dims) | per dim | ☐ |
| QALIS vs HELM mean advantage | ≥ +0.10 (all dims) | per dim | ☐ |
| QALIS vs MLflow mean advantage | ≥ +0.10 (all dims) | per dim | ☐ |
| QALIS mean detection lag | 1.38 h | ± 0.20 h | ☐ |
| ISO25010 mean detection lag | 5.21 h | ± 0.30 h | ☐ |
| HELM mean detection lag | 4.43 h | ± 0.30 h | ☐ |
| Detection lag improvement (vs best baseline) | 68% | ± 8 pp | ☐ |
| Largest effectiveness gap: TI dimension | QALIS 0.78 vs ISO 0.29 | ± 0.05 | ☐ |

**Figure 5** (grouped bar chart):
- [ ] 6 dimension groups, 4 bars each (QALIS + 3 baselines)
- [ ] QALIS bar highest in all 6 groups
- [ ] File written to `analysis/figures/figure5_effectiveness_comparison.pdf`

**Figure 6** (longitudinal line chart):
- [ ] 3 monthly time points (Oct / Nov / Dec 2024)
- [ ] QALIS detection rate line above all baselines
- [ ] File written to `analysis/figures/figure6_longitudinal_detection.pdf`

---

## Statistical Reliability (§3.5)

Run: `python supplementary/replication_package/replicate_all_results.py --target stats --verify`

| Check | Expected value | Tolerance | Pass? |
|-------|----------------|-----------|-------|
| FC-4 Fleiss κ | 0.76 | ± 0.05 | ☐ |
| TI-2 Fleiss κ | 0.71 | ± 0.05 | ☐ |
| TI-3 Cronbach α | 0.84 | ± 0.05 | ☐ |
| Interview IAA Cohen's κ | 0.81 | ± 0.05 | ☐ |

---

## Red-Team Results (Appendix B)

From `red_team/results/`:

| Check | Expected value | Pass? |
|-------|----------------|-------|
| Total injection attempts | 2,850 | ☐ |
| S1 resistance rate | 0.9749 | ☐ |
| S2 resistance rate | 0.9833 | ☐ |
| S3 resistance rate | 0.9777 | ☐ |
| S4 resistance rate | 0.9928 | ☐ |
| All systems pass threshold (S1–S3: ≥0.97; S4: ≥0.99) | True | ☐ |
| Hardest attack category | encoding_obfuscation (2.8%) | ☐ |

---

## Perturbation Tests

From `perturbation_tests/`:

| Check | Expected value | Pass? |
|-------|----------------|-------|
| RO-1 mean sensitivity (all systems) | 0.0688 | ☐ |
| RO-4 mean cosine similarity | ≥ 0.85 | ☐ |
| RO-3 OOD detection rate (all systems) | ≥ 0.80 | ☐ |

---

## Notes

- Tolerances account for floating-point differences across hardware/OS platforms
- Known deviations from paper-printed values are documented in `known_deviations.md`
- If a check fails outside tolerance, consult `known_deviations.md` before raising an issue
