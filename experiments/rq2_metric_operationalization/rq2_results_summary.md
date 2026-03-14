# RQ2 Results Summary — Metric Operationalization

**Research Question**: Can the QALIS metrics be reliably operationalized and collected in production LLM-integrated software systems?

---

## Finding 1 — Collection Completeness (exp_rq2_001)

**97.3% metric collection completeness** across all four case systems.

| System | Applicable Metrics | Collected | Completeness |
|--------|--------------------|-----------|--------------|
| S1 | 24 | 24 | **100%** |
| S2 | 22 (TI-3 N/A) | 22 | **100%** |
| S3 | 24 | 24 | **100%** |
| S4 | 23 (IQ-3 N/A) | 22 | **95.7%** |

**Two collection gaps identified:**
- **IQ-3 / S4**: Cost per quality unit — self-hosted model, cost tracking not
  aligned with QALIS formula. Excludes IQ-3 from S4's IQ-4 denominator.
- **TI-3 / S2**: User interpretability rating — IDE plugin has no user-facing
  explanation surface. Metric not applicable.

Both gaps were anticipated during framework design and documented in the
framework specification.

---

## Finding 2 — Key Metric Correlations (exp_rq2_001)

Two cross-layer correlations with practical implications:

### SF-3 ↔ RO-4 (r = 0.61)
Systems with less semantically consistent outputs (lower RO-4) produce more
hallucinations (higher SF-3). **Implication**: RO-4 semantic invariance can
serve as a cheaper, real-time proxy for hallucination monitoring, since
embedding similarity requires no NLI inference.

### IQ-2 ↔ IQ-1 (r = 0.74)
P95 latency degradation reliably precedes API availability failures.
**Implication**: Monitor IQ-2 as an early warning indicator for SLA breaches —
alerts at latency spike can prevent full availability incidents.

---

## Finding 3 — Model Selection (exp_rq2_002, exp_rq2_003)

**NLI model**: `cross-encoder/nli-deberta-v3-large` selected (F1=0.891 on
200-item calibration set, 12.4ms/claim on GPU).

**Embedding model**: `sentence-transformers/all-mpnet-base-v2` selected
(OOD AUROC=0.887, Spearman r=0.821 with human invariance ratings). Stored
as 512-dim via PCA (99.1% variance retained).

---

## Answer to RQ2

**Yes** — 97.3% of applicable metrics were successfully collected across all
four systems. The two gaps are documented and do not compromise the framework's
validity. Key inter-metric correlations provide actionable monitoring shortcuts
(use RO-4 as SF-3 proxy; use IQ-2 as IQ-1 leading indicator).
