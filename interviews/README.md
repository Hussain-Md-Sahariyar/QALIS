# QALIS Practitioner Interviews

Semi-structured interviews with 14 industry practitioners conducted November–December 2024.
Used to validate QALIS metric relevance, calibrate thresholds, and elicit practitioner
concerns about LLM-integrated software quality.

## Study Design

| Property | Detail |
|----------|--------|
| **n participants** | 14 |
| **Interview type** | Semi-structured, 48–71 min (mean 58 min) |
| **Period** | November 4 – December 4, 2024 |
| **Recording** | Audio-recorded with participant consent |
| **Transcription** | Verbatim with minor disfluency removal |
| **Anonymisation** | Org names, product names, vendor details removed |
| **Analysis method** | Framework method (Ritchie & Spencer, 1994) |
| **Inter-rater reliability** | Cohen's κ = 0.81 (substantial agreement) |

## Participant Sample

| ID | Sector | Role |
|----|--------|------|
| INT-01 | Financial Services | Principal ML Engineer |
| INT-02 | Healthcare | AI Product Manager |
| INT-03 | Legal Tech | Head of LLM Engineering |
| INT-04 | E-Commerce | Senior Data Scientist |
| INT-05 | Software Dev Tooling | ML Platform Engineer |
| INT-06 | Manufacturing | Applied AI Lead |
| INT-07 | Financial Services | LLM Safety Engineer |
| INT-08 | Healthcare | Clinical Informatics Lead |
| INT-09 | Legal Tech | VP of Engineering |
| INT-10 | E-Commerce | ML Engineering Manager |
| INT-11 | Software Dev Tooling | Staff Software Engineer |
| INT-12 | Manufacturing | AI Systems Architect |
| INT-13 | Financial Services | Director of AI |
| INT-14 | Healthcare | Chief Data Officer |

## Structure

```
interviews/
├── README.md                           ← This file
├── interview_metadata.csv              ← Participant and session metadata
├── transcripts/                        ← 14 verbatim transcripts (anonymised)
│   ├── INT-01_transcript.txt
│   └── ... (INT-02 through INT-14)
├── codebook/                           ← 30-code thematic codebook
│   ├── analysis_codebook.csv           ← Human-readable codebook
│   ├── qalis_codebook_v2.json          ← Machine-readable (used by annotation scripts)
│   ├── iaa_coding_log.json             ← Session-level IAA (12 coding sessions)
│   └── README.md
└── thematic_analysis/                  ← Analysis outputs
    ├── README.md
    ├── theme_summary.json              ← 8-theme summary
    ├── coded_excerpts.csv              ← All 237 coded excerpts
    ├── iaa_analysis.json               ← Inter-rater reliability detail
    ├── TH1_theme_report.json           ← Per-theme evidence and significance
    └── ... (TH2 through TH8)
```

## Key Findings

The thematic analysis identified 8 themes across 237 coded excerpts:

1. **TH1** — Existing QA tools inadequate for LLM-specific failures (all 14 participants)
2. **TH2** — Hallucination is the primary safety concern (n=52 excerpts, strongest in healthcare/legal)
3. **TH3** — Transparency is the most underserved quality gap (11/14 unprompted citations)
4. **TH4** — Integration reliability is distinct from model quality (requires separate instrumentation)
5. **TH5** — Domain-specific threshold calibration is essential (generic defaults insufficient)
6. **TH6** — Prompt brittleness is a systematic robustness failure mode
7. **TH7** — Regulatory compliance drives quality investment above baseline
8. **TH8** — Tooling fragmentation is a primary adoption barrier

These findings directly informed the QALIS metric catalogue, threshold defaults,
and domain override design (see `configs/metrics_thresholds.yaml`).
