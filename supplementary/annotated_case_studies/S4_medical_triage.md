# Annotated Case Study: S4 — Medical Triage Assistant

**Paper reference:** §4.5, Table 4, Figure 3  
**Study period:** October 1 – December 31, 2024 (92 days)  
**Observations:** ~850 (daily metric snapshots; 50K query log entries)  
**Anonymization:** All organizational identifiers, patient-adjacent data, and
clinical site details removed per IRB consent (QUATIC-2025-IRB-Annex-B) and
HIPAA data de-identification procedures.

---

## 1. System Description

**Domain:** Clinical decision support — symptom triage and escalation recommendation  
**Architecture:** Llama 3.1 70B quantized (q8, self-hosted on vLLM), agentic with tool-use  
**Tools:** ICD-10 lookup, drug-interaction checker, NEWS2/MEWS triage score calculator, escalation pathway API  
**Scale:** ~620 daily active users (clinical staff); safety-critical context  
**Team:** 14 engineers (ML + clinical informatics)  
**Risk level:** High (clinical decision support; HIPAA-regulated; patient-safety implications)

The system assists clinical staff (nurses, triage coordinators) in assessing symptom
severity and recommending escalation pathways. It does not make autonomous decisions —
all recommendations are reviewed by a clinician before action. The self-hosted
architecture was mandated by HIPAA data residency requirements.

---

## 2. QALIS Metric Configuration

**Metrics collected:** 23 of 24  
**Excluded:**  
- IQ-3 (Cost per Query): self-hosted; no per-query billing

**Key threshold overrides from defaults:**

| Metric | Default | S4 Override | Rationale |
|--------|---------|-------------|-----------|
| FC-1 Task Accuracy | ≥0.85 | ≥0.80 | Clinical tasks are harder; human-in-the-loop provides safety backstop |
| SF-3 Hallucination Rate | ≤0.020/1K | ≤0.012/1K | Strictest threshold in cohort — clinical hallucinations are safety-critical |
| SS-2 PII Leakage Rate | ≤0.001 | ≤0.0001 | HIPAA compliance; 10× stricter than default |
| SS-4 Policy Compliance | ≥0.98 | ≥0.995 | Medical policies (escalation protocols, contraindications) must be respected |
| TI-4 Audit Trail Completeness | ≥0.95 | ≥1.00 | HIPAA requires complete audit trail for every interaction |
| IQ-2 Latency P95 | ≤1500ms | ≤3000ms | Self-hosted quantized model is slower; clinician accepts higher latency |

---

## 3. Empirical Results (Table 4)

### 3.1 Dimension Scores (monthly means, 0–10 scale)

| Dimension | Month 1 | Month 2 | Month 3 | Overall | Δ M1→M3 |
|-----------|---------|---------|---------|---------|---------|
| FC | 6.91 | 7.31 | 7.11 | **7.1** | +0.20 |
| RO | 8.11 | 8.41 | 8.41 | **8.3** | +0.30 |
| SF | 8.41 | 8.71 | 8.71 | **8.6** | +0.30 |
| SS | 9.11 | 9.21 | 9.31 | **9.2** | +0.20 |
| TI | 8.71 | 8.91 | 9.01 | **8.9** | +0.30 |
| IQ | 6.61 | 6.81 | 7.01 | **6.8** | +0.40 |
| **Composite** | **7.98** | **8.23** | **8.26** | **8.15** | +0.28 |

### 3.2 Metric-level highlights

**SS dimension: 9.2 — highest in cohort (best safety performance)**  
The team invested heavily in safety instrumentation. SS-2 PII leakage rate was 0.00004 —
well below the 0.0001 HIPAA threshold. SS-4 Policy Compliance reached 0.997, achieved
through an extensive policy ruleset (`configs/classifier_config.yaml` — healthcare domain).

**TI dimension: 8.9 — highest in cohort (best transparency performance)**  
Agentic tool-use naturally produces explanation traces (tool call chains, reasoning steps,
triage score derivations). TI-1 Explanation Coverage reached 0.94 — nearly every response
included a structured reasoning trace. Clinical staff rated interpretability at 4.6/5.0 (TI-3).

**RO dimension: 8.3 — highest in cohort (best robustness)**  
Self-hosted Llama 3.1 70B showed exceptional robustness to perturbations. The model's
conservative instruction-following (fine-tuned for clinical conservatism) produces
consistent outputs across paraphrase and typographic perturbations.

**FC-1 (Task Accuracy): 0.801 — narrowly above 0.80 threshold**  
Lowest FC-1 in cohort. Clinical triage tasks are genuinely harder than the other domains.
The model occasionally misclassified low-acuity presentations as medium-acuity. The
human-in-the-loop safety backstop was invoked in 2.3% of cases.

**IQ-2 (Latency P95): 2,847ms — within 3000ms threshold but highest latency in cohort**  
Self-hosted quantized model + agentic tool calls produce high latency. Three tool calls
per interaction (on average) account for ~1,200ms. Clinicians reported that latency was
acceptable given the decision-support (non-real-time) context.

**SF-3 (Hallucination Rate): 0.010/1K tokens — below strict 0.012 threshold**  
Best SF-3 performance relative to threshold. Self-hosted model fine-tuned on
clinical guidelines shows fewer hallucinated drug names or procedure codes than
general-purpose models.

---

## 4. Quality Incidents

**Total incidents detected:** 4 over 92 days  
**Incidents detected first by QALIS:** 4/4 (100%)  
**Mean QALIS detection lead over baseline:** +7.1 days (highest in cohort)

Notable incidents:

| Date | Metric | Description | Detection method |
|------|--------|-------------|-----------------|
| Oct 25 | TI-4 | Audit trail gap — 3 interactions missing complete audit records after a vLLM upgrade | QALIS daily audit check |
| Nov 08 | FC-1 | Accuracy drop (0.801→0.762) following ICD-10 code table update; model citing deprecated codes | QALIS daily batch |
| Nov 08 | SF-3 | Correlated hallucination spike with same ICD-10 update — deprecated codes misidentified as valid | QALIS daily batch |
| Dec 17 | SS-4 | Policy violation rate elevated (0.009) — model producing recommendations outside escalation protocol | QALIS CI quality gate |

---

## 5. Practitioner Observations

Observations from practitioner interviews (INT-12, INT-13) and annotated team retros:

- The correlated FC-1/SF-3 incident on Nov 8 was the most significant finding: a
  knowledge base update (ICD-10 codes) caused simultaneous drops in accuracy and
  faithfulness. Neither incident would have been detected by the team's existing
  monitoring within 7 days (their infrastructure dashboard only tracks API latency and errors).
- The HIPAA-compliant TI-4 audit completeness check was cited as uniquely valuable:
  *"No other tool we've evaluated automatically verifies that every interaction has
  all 13 required audit fields. That's a regulatory requirement we can now monitor continuously."*
- Self-hosting Llama 3.1 70B was validated as the right architectural choice for this
  domain: SS and RO dimensions both scored highest in the cohort, attributed to the
  conservative fine-tuning and data residency guarantees.

---

## 6. Configuration Files

| File | Contents |
|------|----------|
| `configs/system_profiles/S4_medical_triage.yaml` | Full system profile including HIPAA settings |
| `configs/classifier_config.yaml` (healthcare section) | SS-4 policy ruleset |
| `data/perturbation_tests/S4/` | RO-1, RO-3, RO-4 perturbation results |
| `red_team/results/S4_redteam_summary.json` | RO-2, SS-3 red-team results |
| `data/annotations/FC4_factual_precision/fc4_all_systems_combined.csv` | FC-4 annotation panel (S4 rows) |
