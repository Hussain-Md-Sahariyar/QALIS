# QALIS — Supplementary Materials

Supplementary materials for the QUATIC 2025 paper:

> *"QALIS: A Multi-Dimensional Quality Assessment Framework for Large Language
> Model-Integrated Software Systems"*

---

## Structure

```
supplementary/
├── README.md                              ← This file
│
├── case_study_protocol/                   ← §3 Research methodology
│   ├── README.md
│   ├── case_study_protocol.md             ← Full case study research protocol
│   ├── consent_form_template.md           ← Participant consent form (anonymised)
│   ├── data_management_plan.md            ← Data storage, retention, access policy
│   └── irb_approval_summary.md            ← IRB approval summary (ref: QUATIC-2025-IRB-Annex-B)
│
├── survey_instruments/                    ← §3.4–3.5 Data collection instruments
│   ├── README.md
│   ├── practitioner_interview_guide.txt   ← Semi-structured interview guide (14 participants)
│   ├── annotator_training_guide.md        ← FC-4 / TI-2 annotator onboarding guide
│   ├── annotation_rubric_fc4.md           ← FC-4 Factual Precision annotation rubric
│   ├── annotation_rubric_ti2.md           ← TI-2 Explanation Faithfulness annotation rubric
│   └── ti3_interpretability_survey.md     ← TI-3 User Interpretability Likert survey
│
└── replication_package/                   ← Full replication support
    ├── README.md
    ├── data_dictionary.json               ← Schema for all 15 data files
    ├── replicate_all_results.py           ← End-to-end replication script
    ├── environment.yml                    ← Conda environment specification
    ├── replication_checklist.md           ← Step-by-step verification checklist
    └── known_deviations.md               ← Documented deviations and caveats
```

## Quick Replication

```bash
# 1. Create environment
conda env create -f supplementary/replication_package/environment.yml
conda activate qalis-replication

# 2. Run full replication pipeline
python supplementary/replication_package/replicate_all_results.py

# Expected runtime: 8–15 minutes (CPU) | 3–5 minutes (GPU)
```

## Paper Section Cross-Reference

| Supplementary file | Paper section |
|-------------------|---------------|
| `case_study_protocol.md` | §3.1–3.2 (Research design) |
| `consent_form_template.md` | §3.4 (Ethical considerations) |
| `irb_approval_summary.md` | §3.4 (Ethical considerations) |
| `practitioner_interview_guide.txt` | §3.4 (Interview protocol) |
| `annotator_training_guide.md` | §3.5 (Human annotation protocol) |
| `annotation_rubric_fc4.md` | §3.5, Table 3 (FC-4) |
| `annotation_rubric_ti2.md` | §3.5, Table 3 (TI-2) |
| `ti3_interpretability_survey.md` | §3.5, Table 3 (TI-3) |
| `data_dictionary.json` | §3.3, Appendix A |
| `replication_checklist.md` | Appendix B |
| `known_deviations.md` | §7 (Threats to validity) |

## Contact

For replication questions, open a GitHub Issue or contact the corresponding author.
(Author details withheld for double-blind review; will be disclosed on acceptance.)
