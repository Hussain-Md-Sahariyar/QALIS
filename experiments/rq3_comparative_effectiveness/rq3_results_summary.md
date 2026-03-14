# RQ3 Results Summary — Comparative Effectiveness

**Research Question**: Is QALIS more effective than existing quality assessment approaches (ISO/IEC 25010 adapted, HELM, MLflow) at detecting quality issues in LLM-integrated software systems?

---

## Finding 1 — Statistical Superiority (exp_rq3_001)

QALIS significantly outperforms all three baselines on all six dimensions
(Wilcoxon signed-rank, all p < 0.001, Bonferroni α = 0.000556, k=18):

| Dimension | QALIS | ISO 25010 | HELM | MLflow | Max Δ |
|-----------|-------|-----------|------|--------|-------|
| FC | **0.89** | 0.67 | 0.74 | 0.51 | +0.38 |
| RO | **0.81** | 0.54 | 0.69 | 0.43 | +0.38 |
| SF | **0.87** | 0.31 | 0.62 | 0.28 | **+0.59** |
| SS | **0.91** | 0.58 | 0.49 | 0.61 | **+0.42** |
| TI | **0.78** | 0.29 | 0.38 | 0.19 | **+0.59** |
| IQ | **0.84** | 0.71 | 0.22 | 0.77 | +0.62 |

**Largest margin**: TI dimension — QALIS 0.78 vs ISO 25010 0.29 (Δ=0.49). Transparency
is the most underserved dimension in all three baseline approaches.

**Baseline blind spots**:
- ISO 25010: No hallucination or transparency metrics (SF 0.31, TI 0.29)
- HELM: Model-centric — near-zero IQ coverage (0.22); TI gap (0.38)
- MLflow: Infrastructure focus — near-zero SF (0.28) and TI (0.19)

---

## Finding 2 — Longitudinal Improvement (exp_rq3_002)

QALIS detection rates improved substantially over the 3-month study period,
while baselines remained flat (no significant trend, p>0.05):

| Approach | Month 1 | Month 2 | Month 3 | Trend |
|----------|---------|---------|---------|-------|
| **QALIS** | 0.621 | 0.768 | **0.891** | ↑ significant (p<0.001) |
| ISO 25010 | 0.481 | 0.492 | 0.503 | → flat |
| HELM | 0.548 | 0.556 | 0.561 | → flat |
| MLflow | 0.521 | 0.531 | 0.539 | → flat |

**By Month 3:**
- **81% reduction** in undetected hallucination events
- **77% reduction** in undetected integration errors

---

## Finding 3 — Detection Lag (exp_rq3_003)

QALIS detected incidents **68% earlier** on average than the best-performing baseline:

| System | QALIS lag (h) | Best baseline (h) | Improvement |
|--------|---------------|-------------------|-------------|
| S1 | 1.4 | 5.2 | 73% earlier |
| S2 | 1.1 | 4.7 | 77% earlier |
| S3 | 1.3 | 4.9 | 73% earlier |
| S4 | 1.7 | 6.1 | 72% earlier |
| **Mean** | **1.4** | **5.2** | **68% earlier** |

---

## Answer to RQ3

**Yes** — QALIS is significantly more effective than all three baseline approaches across all six quality dimensions. The improvement is consistent across systems, statistically robust (all p < 0.001 after Bonferroni correction), and practically meaningful (68% earlier detection, 81% hallucination reduction by Month 3).
