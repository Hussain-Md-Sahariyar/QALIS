# RQ1 Results Summary — Dimension Coverage

**Research Question**: Do the six QALIS dimensions collectively capture distinct,
non-redundant aspects of quality in LLM-integrated software systems?

---

## Finding 1 — Dimension Independence (exp_rq1_001)

Inter-dimension Pearson correlations across 3,400 observations:

| | FC | RO | SF | SS | TI | IQ |
|--|----|----|----|----|----|----|
| **FC** | - | 0.28 | 0.34 | 0.21 | 0.19 | 0.31 |
| **RO** | | - | 0.33 | 0.27 | 0.22 | 0.18 |
| **SF** | | | - | 0.29 | 0.35 | 0.24 |
| **SS** | | | | - | 0.31 | 0.26 |
| **TI** | | | | | - | 0.38 |
| **IQ** | | | | | | - |

**Median |r| = 0.31** - well below the 0.50 threshold for redundancy.
**Max |r| = 0.38** - no dimension pair is redundant.

**Hypothesis supported**: QALIS dimensions are statistically non-redundant.

---

## Finding 2 — Dimension Activation (exp_rq1_002)

All six dimensions identified quality deficiencies in all four case systems:

| Dimension | S1 | S2 | S3 | S4 | Active in N systems |
|-----------|----|----|----|----|---------------------|
| FC | ✓ | ✓ | ✓ | ✓ | **4/4** |
| RO | ✓ | ✓ | ✓ | ✓ | **4/4** |
| SF | ✓ | ✓ | ✓ | ✓ | **4/4** |
| SS | ✓ | ✓ | ✓ | ✓ | **4/4** |
| TI | ✓ | ✓ | ✓ | ✓ | **4/4** |
| IQ | ✓ | ✓ | ✓ | ✓ | **4/4** |

All dimensions active in all systems exceeds the paper's stated threshold of ≥3/4.

---

## Answer to RQ1

**Yes** — the six QALIS dimensions collectively provide a non-redundant,
comprehensive assessment of LLM-integrated software quality, with each dimension
capturing distinct quality concerns across all four case systems studied.

Key evidence:
- Median |r| = 0.31 between dimensions (confirms non-redundancy)
- All dimensions active in all 4 systems (confirms coverage breadth)
- Dimension dropout ablation (exp_abl_001) confirms each dimension contributes
  to composite validity — removing any single dimension degrades detection rate
