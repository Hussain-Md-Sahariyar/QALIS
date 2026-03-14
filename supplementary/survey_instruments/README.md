# Survey Instruments

Data collection instruments for the QALIS empirical evaluation.

## Files

| File | Purpose | Paper section |
|------|---------|---------------|
| `practitioner_interview_guide.txt` | Semi-structured guide for 14 practitioner interviews | §3.4 |
| `annotator_training_guide.md` | Onboarding guide for FC-4 and TI-2 annotation panels | §3.5 |
| `annotation_rubric_fc4.md` | Detailed FC-4 Factual Precision annotation rubric | §3.5, Table 3 |
| `annotation_rubric_ti2.md` | Detailed TI-2 Explanation Faithfulness annotation rubric | §3.5, Table 3 |
| `ti3_interpretability_survey.md` | TI-3 User Interpretability Likert survey instrument | §3.5, Table 3 |

## Overview

### Practitioner Interviews

14 semi-structured interviews (48–71 min, mean 58 min) conducted November–December 2024.
IRB-approved (QUATIC-2025-IRB-Annex-B). Audio-recorded with participant consent.
Analysis: framework method (Ritchie & Spencer, 1994), Cohen's κ = 0.81.

### Human Annotation

Two metrics required independent human judgment:

| Metric | Items | IAA Achieved | Target |
|--------|-------|-------------|--------|
| FC-4 Factual Precision | 800 | Fleiss κ = 0.76 | κ ≥ 0.70 ✓ |
| TI-2 Explanation Faithfulness | 500 | Fleiss κ = 0.71 | κ ≥ 0.70 ✓ |

One metric used a Likert survey:

| Metric | Participants | Reliability |
|--------|-------------|-------------|
| TI-3 User Interpretability | 14 (same as interview cohort) | Cronbach α = 0.84 |

Annotation configuration: `configs/annotation_config.yaml`
