# Annotated Case Study: S2 — AI Code Assistant (IDE Plugin)

**Paper reference:** §4.3, Table 4, Figure 3  
**Study period:** October 1 – December 31, 2024 (92 days)  
**Observations:** ~850 (daily metric snapshots; 50K query log entries)  
**Anonymization:** All organizational identifiers removed per IRB consent (QUATIC-2025-IRB-Annex-B)

---

## 1. System Description

**Domain:** Code generation and completion (IDE plugin)  
**Architecture:** Claude 3.5 Sonnet (fine-tuned on internal codebase) + FIM (fill-in-middle), streaming responses  
**Scale:** ~3,200 daily active users, IDE-integrated (VS Code, JetBrains)  
**Team:** 7 engineers  
**Risk level:** Medium (code quality risk; no regulated data)

The system provides inline code completion, docstring generation, test case suggestion,
and natural-language-to-code translation. The fine-tuned model improves performance on
the organization's internal libraries and coding conventions. Streaming (token-by-token)
delivery is used for user-perceived latency reduction.

---

## 2. QALIS Metric Configuration

**Metrics collected:** 23 of 24  
**Excluded:**  
- TI-3 (User Interpretability): no direct user-facing explanation interface at the IDE layer; code is self-explanatory  

**Key threshold overrides from defaults:**

| Metric | Default | S2 Override | Rationale |
|--------|---------|-------------|-----------|
| FC-1 Task Accuracy | ≥0.85 | ≥0.88 | Executable oracle available; stricter bar justified |
| FC-2 BERTScore F1 | ≥0.78 | Not applicable | Code domain; FC-3 (Pass@k) is the primary correctness metric |
| FC-3 Pass@k (k=5) | ≥0.90 | ≥0.90 (no change) | Unit test oracle; default appropriate |
| IQ-2 Latency P95 | ≤1500ms | ≤2000ms | Streaming TTFT is <300ms; total latency higher but acceptable |

---

## 3. Empirical Results (Table 4)

### 3.1 Dimension Scores (monthly means, 0–10 scale)

| Dimension | Month 1 | Month 2 | Month 3 | Overall | Δ M1→M3 |
|-----------|---------|---------|---------|---------|---------|
| FC | 8.71 | 8.89 | 9.09 | **8.9** | +0.38 |
| RO | 7.63 | 7.91 | 7.81 | **7.8** | +0.18 |
| SF | 7.11 | 7.52 | 7.29 | **7.3** | +0.18 |
| SS | 8.69 | 8.91 | 8.81 | **8.8** | +0.12 |
| TI | 6.01 | 6.31 | 6.31 | **6.2** | +0.30 |
| IQ | 7.01 | 7.21 | 7.11 | **7.1** | +0.10 |
| **Composite** | **7.53** | **7.79** | **7.74** | **7.68** | +0.21 |

### 3.2 Metric-level highlights

**FC-1 (Task Accuracy): 0.898 (above 0.88 threshold)**  
Highest FC-1 score in the cohort. The fine-tuned model and executable unit-test oracle
provide a reliable signal. FC-3 Pass@5 reached 0.932 — the fine-tuning on internal
libraries shows a clear benefit over base Claude 3.5.

**SF-3 (Hallucination Rate): 0.031/1K tokens — above default threshold (0.020)**  
Highest hallucination rate in the cohort. The code domain is inherently prone to
hallucinated API references, non-existent library functions, and incorrect
parameter signatures. Standard NLI grounding is harder to apply to code.  
*Root cause annotation:* 61% of hallucinations were hallucinated function/method names
that do not exist in the imported libraries. A post-generation AST parsing step was
added in Month 3 (partial mitigation; SF-3 dropped to 0.025 but still above threshold).

**RO-2 (Injection Resistance): 0.974**  
Strong resistance to prompt injection. The fine-tuned model was less susceptible to
role-play bypass and direct instruction override categories (red-team data:
`red_team/results/S2_redteam_summary.json`).

**TI-4 (Audit Trail Completeness): 0.88**  
Lowest TI score. IDE plugin logging was incomplete — session context was not always
propagated to the audit log. Resolved in a deployment update (Week 7).

---

## 4. Quality Incidents

**Total incidents detected:** 8 over 92 days  
**Incidents detected first by QALIS:** 7/8 (87.5%)  
**Mean QALIS detection lead over baseline:** +5.1 days

Notable incidents:

| Date | Metric | Description | Detection method |
|------|--------|-------------|-----------------|
| Oct 22 | SF-3 | Hallucination spike following library version update (numpy 1.x → 2.x API changes) | QALIS daily batch |
| Nov 11 | FC-3 | Pass@5 drop (0.932→0.881) after fine-tune checkpoint rollback | QALIS CI quality gate |
| Dec 01 | IQ-4 | Audit trail gap discovered — 12% of sessions missing log entries | QALIS weekly audit check |

---

## 5. Practitioner Observations

Observations from practitioner interview (INT-07) and team retrospective notes:

- The SF-3 hallucination problem in code generation was identified as a fundamental
  challenge: NLI models trained on natural language do not reliably identify hallucinated
  code constructs. The team explored AST-based verification as a domain-specific extension.
- FC-3 Pass@k was unanimously the most actionable metric for the development team —
  directly tied to developer productivity metrics.
- *"The IQ-4 audit gap would never have been found by our existing monitoring stack.
  Only QALIS tracks whether every field in the schema is populated."*

---

## 6. Configuration Files

| File | Contents |
|------|----------|
| `configs/system_profiles/S2_code_assistant.yaml` | Full system profile |
| `data/perturbation_tests/S2/` | RO-1, RO-3, RO-4 perturbation results |
| `red_team/results/S2_redteam_summary.json` | RO-2, SS-3 red-team results |
| `data/annotations/FC4_factual_precision/fc4_all_systems_combined.csv` | FC-4 annotation panel (S2 rows) |
