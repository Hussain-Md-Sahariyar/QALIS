# Annotated Case Study: S1 — Customer Support Chatbot

**Paper reference:** §4.2, Table 4, Figure 3  
**Study period:** October 1 – December 31, 2024 (92 days)  
**Observations:** ~850 (daily metric snapshots; 50K query log entries)  
**Anonymization:** All organizational identifiers, product names, and vendor contracts removed per IRB consent agreement (QUATIC-2025-IRB-Annex-B)

---

## 1. System Description

**Domain:** E-commerce customer support  
**Architecture:** GPT-4o (OpenAI API) + Dense-passage RAG (Pinecone vector store, top-5 retrieval)  
**Scale:** ~8,400 daily active users, 42 peak RPS, mean 3.8 turns per session  
**Team:** 11 engineers (ML + backend)  
**Risk level:** Medium (no regulated data; reputational risk from incorrect product/policy answers)

The system responds to customer queries about orders, returns, product specifications,
and account management. Responses are grounded in a proprietary knowledge base
(~240K documents). A re-ranker (ms-marco-MiniLM-L-6-v2) improves retrieval precision
before the final prompt is assembled.

---

## 2. QALIS Metric Configuration

**Metrics collected:** 22 of 24  
**Excluded:**  
- IQ-3 (Cost per Query): billing data alignment with provider invoices not achieved during study period  

**Key threshold overrides from defaults:**

| Metric | Default | S1 Override | Rationale |
|--------|---------|-------------|-----------|
| FC-1 Task Accuracy | ≥0.85 | ≥0.85 (no change) | General QA domain; default appropriate |
| SF-3 Hallucination Rate | ≤0.020/1K | ≤0.018/1K | RAG system; stricter given context availability |
| SS-1 Toxicity Rate | ≤0.005 | ≤0.005 (no change) | Consumer-facing; default appropriate |
| IQ-2 Latency P95 | ≤1500ms | ≤1800ms | RAG + re-ranker adds ~300ms overhead; adjusted accordingly |

---

## 3. Empirical Results (Table 4)

### 3.1 Dimension Scores (monthly means, 0–10 scale)

| Dimension | Month 1 | Month 2 | Month 3 | Overall | Δ M1→M3 |
|-----------|---------|---------|---------|---------|---------|
| FC | 7.39 | 8.59 | 8.50 | **7.8** | +1.11 |
| RO | 6.40 | 6.21 | 6.02 | **6.2** | −0.38 |
| SF | 7.91 | 8.37 | 8.12 | **8.1** | +0.21 |
| SS | 7.29 | 7.54 | 7.49 | **7.4** | +0.20 |
| TI | 5.21 | 5.83 | 5.72 | **5.6** | +0.51 |
| IQ | 8.41 | 8.12 | 8.41 | **8.3** | 0.00 |
| **Composite** | **7.10** | **7.44** | **7.38** | **7.23** | +0.28 |

### 3.2 Metric-level highlights

**FC-1 (Task Accuracy): 0.831 → 0.891 (Months 1–3)**  
Month 1 performance was below the 0.85 threshold. Root cause: retrieval quality issues
identified via low SF-1 (faithfulness 0.71) — model was hallucinating when retrieved
chunks were irrelevant. RAG re-ranker threshold was tuned from 0.30 to 0.45 (Week 6),
producing the Month 2 recovery to 0.891.  
*Annotation evidence: FC-4 Factual Precision panel (800 claims) confirmed 23% of
Month-1 errors were attributable to unsupported factual claims.*

**RO-1 (Perturbation Sensitivity): 0.142 (above threshold ≤0.12)**  
S1 was the weakest system on robustness. Typographic perturbations (typo corpus,
5K test cases) caused measurable accuracy drops. Threshold violated in all three months.
GPT-4o's performance on typo-corrupted inputs was notably worse than expected — this
aligns with the model's training data distribution.  
*Perturbation data: `data/perturbation_tests/S1/typographical_perturbations.csv`*

**SF-3 (Hallucination Rate): 0.017/1K tokens**  
Below the tightened 0.018 threshold. NLI model (DeBERTa-v3-large) identified
contradicted claim-context pairs. 68% of hallucinations occurred when retrieved
context contained partial but incomplete information (retrieval quality issue).  
*NLI evidence: `data/raw/S1_Customer_Support_Chatbot/query_logs/nli_analysis_log.jsonl`*

**TI-1 (Explanation Coverage): 0.56**  
Lowest-scoring metric. The system rarely provided reasoning traces or confidence
signals. Practitioners in this sector did not mandate explanations, which explains
the low baseline.

---

## 4. Quality Incidents

**Total incidents detected:** 12 over 92 days  
**Incidents detected first by QALIS:** 9/12 (75%)  
**Mean QALIS detection lead over baseline:** +4.8 days

Notable incidents:

| Date | Metric | Description | Detection method |
|------|--------|-------------|-----------------|
| Oct 14 | SF-3 | Hallucination spike (+0.009/1K) following RAG index update | QALIS daily batch |
| Nov 02 | IQ-2 | P95 latency breach (>1800ms) — Pinecone region issue | QALIS real-time |
| Nov 28 | RO-2 | 3 successful prompt injections in 48hr window | Red-team weekly scan |
| Dec 09 | FC-1 | Accuracy drop post prompt-template update (v1.2→v1.3) | QALIS CI quality gate |

---

## 5. Practitioner Observations

Observations sourced from anonymized practitioner interviews (INT-01, INT-04) and
annotated team retrospective meeting notes (consent obtained):

- *"We didn't realise our retrieval quality was affecting hallucination rates until
  the SF-1 and SF-3 metrics were surfaced side-by-side."* — ML Lead, S1 team
- The team adopted QALIS's daily hallucination monitoring as part of their regular
  on-call runbook after Month 1.
- Transparency (TI) was identified as a future improvement priority. Team planned
  TI-1 improvements (structured reasoning output) for Q1 2025.

---

## 6. Configuration Files

| File | Contents |
|------|----------|
| `configs/system_profiles/S1_customer_support.yaml` | Full system profile |
| `configs/metrics_thresholds.yaml` (S1 section) | Threshold overrides |
| `data/annotations/FC4_factual_precision/fc4_all_systems_combined.csv` | FC-4 annotation panel (S1 rows) |
| `data/perturbation_tests/S1/` | RO-1, RO-3, RO-4 perturbation results |
| `red_team/results/S1_redteam_summary.json` | RO-2, SS-3 red-team results |
