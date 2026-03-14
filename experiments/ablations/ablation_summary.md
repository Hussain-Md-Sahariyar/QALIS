# Ablation Studies Summary

## exp_abl_001 — Dimension Dropout

Removing **SS** or **SF** causes the largest drop in detection rate (>8 pp).
Even removing **TI** (smallest impact) causes 2.2 pp drop. All six dimensions
are necessary for full detection capability.

| Excluded | Detection Rate | Δ vs Full | Impact |
|----------|---------------|-----------|--------|
| None (full) | 0.891 | — | — |
| SS | 0.798 | −0.093 | **High** |
| SF | 0.802 | −0.089 | **High** |
| FC | 0.841 | −0.050 | Medium |
| IQ | 0.851 | −0.040 | Medium |
| RO | 0.863 | −0.028 | Low |
| TI | 0.869 | −0.022 | Low |

## exp_abl_002 — Metric Subset (FC)

Minimum viable sets by deployment type:
- **Non-code systems**: FC-1 + FC-4 (validity 0.91, 50% cost reduction)
- **Code systems**: FC-1 + FC-3 + FC-4 (validity 0.95, 25% reduction)
- **High-risk**: Full set FC-1 through FC-4

## exp_abl_003 — Weight Sensitivity

Composite ranking is robust to dimension weight perturbations. S4 remains
top-ranked under 4 of 5 tested weight schemes. Equal weighting (default) is
the most defensible absent domain-specific guidance.
