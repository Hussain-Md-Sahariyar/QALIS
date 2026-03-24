# Annotated Case Study: S3 — Document Summarization and QA

**Paper reference:** §4.4, Table 4, Figure 3  
**Study period:** October 1 – December 31, 2024 (92 days)  
**Observations:** ~850 (daily metric snapshots; 50K query log entries)  
**Anonymization:** All organizational identifiers removed per IRB consent (QUATIC-2025-IRB-Annex-B)

---

## 1. System Description

**Domain:** Document intelligence — summarization and question-answering over uploaded documents  
**Architecture:** Gemini 1.5 Pro (Google API) + Long-context RAG (1M token window), chunked retrieval for precision  
**Scale:** ~1,900 daily active users; typical documents 50–400 pages  
**Team:** 5 engineers  
**Risk level:** Medium (document confidentiality risk; no regulated data)

The system accepts uploaded PDFs, DOCX, and TXT documents, then answers user questions
and produces structured summaries. Gemini 1.5 Pro's 1M token context window enables
full-document ingestion for short documents; a sliding-window RAG approach is used for
documents >128K tokens. The system targets legal, financial, and research document users.

---

## 2. QALIS Metric Configuration

**Metrics collected:** 24 of 24 (complete coverage — only system in cohort with full coverage)

**Key threshold overrides from defaults:**

| Metric | Default | S3 Override | Rationale |
|--------|---------|-------------|-----------|
| SF-1 Faithfulness NLI | ≥0.75 | ≥0.80 | Full document context available; no retrieval gap excuse |
| SF-3 Hallucination Rate | ≤0.020/1K | ≤0.015/1K | Strictest in cohort; grounded document QA must be faithful |
| TI-1 Explanation Coverage | ≥0.65 | ≥0.70 | User explicitly expects source citation in document QA |
| SF-2 Attribution Coverage | ≥0.80 | ≥0.85 | Document QA must cite document sections |

---

## 3. Empirical Results (Table 4)

### 3.1 Dimension Scores (monthly means, 0–10 scale)

| Dimension | Month 1 | Month 2 | Month 3 | Overall | Δ M1→M3 |
|-----------|---------|---------|---------|---------|---------|
| FC | 8.01 | 8.31 | 8.41 | **8.2** | +0.40 |
| RO | 6.61 | 6.91 | 6.81 | **6.8** | +0.20 |
| SF | 8.91 | 9.11 | 9.31 | **9.1** | +0.40 |
| SS | 7.71 | 8.01 | 7.91 | **7.9** | +0.20 |
| TI | 7.31 | 7.61 | 7.61 | **7.5** | +0.30 |
| IQ | 8.51 | 8.71 | 8.61 | **8.6** | +0.10 |
| **Composite** | **7.84** | **8.11** | **8.11** | **8.02** | +0.27 |

### 3.2 Metric-level highlights

**SF dimension: 9.1 — highest in cohort**  
The full-document-context architecture produces exceptional faithfulness. With the
source document available verbatim, the NLI model consistently confirms claims as
entailed. SF-1 Faithfulness NLI reached 0.913 — the system almost never contradicts
its own source material.

**SF-2 (Attribution Coverage): 0.891**  
The system was configured to always include section/page references. Structured output
format (JSON with `source_sections` field) made this metric straightforwardly measurable.

**RO-1 (Perturbation Sensitivity): 0.138 — above threshold (≤0.12)**  
Document-anchored QA remains susceptible to question rephrasing. When the same question
is asked differently (paraphrase corpus, RO-4), answers diverge in 13.8% of cases.
The long-context model does not always resolve paraphrases to the same document span.
*Perturbation data: `data/perturbation_tests/S3/paraphrase_pairs.csv`*

**TI-3 (User Interpretability): 3.9/5.0 — highest in cohort**  
Document QA users rated response interpretability highest. Explicit source citations
and section references give users clear verification paths. Cronbach α = 0.84 across
14 raters (same practitioner cohort as interviews).

---

## 4. Quality Incidents

**Total incidents detected:** 6 over 92 days  
**Incidents detected first by QALIS:** 6/6 (100%)  
**Mean QALIS detection lead over baseline:** +6.2 days

Notable incidents:

| Date | Metric | Description | Detection method |
|------|--------|-------------|-----------------|
| Oct 31 | RO-3 | OOD rate spike — users uploading non-text images; model produced confabulated descriptions | QALIS daily OOD scan |
| Nov 19 | IQ-2 | Latency P95 breach (>2800ms) — Gemini API rate limiting under load | QALIS real-time |
| Dec 14 | SF-3 | Hallucination spike (0.021) when processing scanned PDFs with OCR errors | QALIS daily batch |

---

## 5. Practitioner Observations

Observations from practitioner interview (INT-09) and annotated retros:

- S3's high SF scores validated the core architecture hypothesis: grounding the model
  in the full document dramatically reduces hallucination risk compared to retrieval-only approaches.
- The OOD incident (image uploads) led to a pre-upload content-type validation step — a
  Layer 1 input quality control not present in the original design.
- *"Six incidents, all caught first by QALIS — our old Datadog dashboards would have
  caught maybe two of these (the latency one and maybe one other)."*

---

## 6. Configuration Files

| File | Contents |
|------|----------|
| `configs/system_profiles/S3_document_summarization.yaml` | Full system profile |
| `data/perturbation_tests/S3/` | RO-1, RO-3, RO-4 perturbation results |
| `red_team/results/S3_redteam_summary.json` | RO-2, SS-3 red-team results |
| `data/annotations/TI3_user_interpretability/ti3_all_systems_combined.csv` | TI-3 survey ratings (S3 rows) |
