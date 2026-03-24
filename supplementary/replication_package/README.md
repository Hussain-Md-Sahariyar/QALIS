# QALIS Replication Package

Full replication support for the QUATIC 2025 paper:

> *"QALIS: A Multi-Dimensional Quality Assessment Framework for Large Language
> Model-Integrated Software Systems"*

---

## Contents

| File | Description |
|------|-------------|
| `data_dictionary.json` | Schema documentation for all 15 data files (Appendix A) |
| `replicate_all_results.py` | End-to-end replication script — reproduces all tables and figures |
| `environment.yml` | Conda environment specification (Python 3.11, pinned deps) |
| `replication_checklist.md` | Step-by-step verification checklist with expected values |
| `known_deviations.md` | Documented deviations between replication outputs and paper |

---

## Quick Start

### 1. Create the environment

```bash
conda env create -f supplementary/replication_package/environment.yml
conda activate qalis-replication
```

### 2. Install the QALIS package

```bash
pip install -e .   # from repository root
```

### 3. Run the full replication

```bash
python supplementary/replication_package/replicate_all_results.py
```

Expected runtime: **8–15 minutes** (CPU) | **3–5 minutes** (GPU available)

### 4. Verify outputs

Compare console output against `replication_checklist.md`. All key values
should match within the tolerances documented there.

---

## What Gets Reproduced

| Result | Script / Module | Expected value |
|--------|----------------|----------------|
| Table 4 — Composite scores | `analysis/rq1/` | S1=7.23, S2=7.68, S3=8.02, S4=8.15 |
| Table 4 — Dim. independence | `analysis/rq1/` | Median \|r\| = 0.31 |
| Figure 4 — Key correlations | `analysis/rq2/` | SF-3↔RO-4: r=−0.61; IQ-2↔IQ-1: r=−0.74 |
| Table 5 — Wilcoxon tests | `analysis/rq3/` | All 18 comparisons p < 0.000556 |
| Figure 5 — Effectiveness gap | `analysis/rq3/` | QALIS mean advantage ≥ +0.20 on all dims |
| Figure 6 — Detection lag | `analysis/rq3/` | QALIS 1.38h vs baseline mean 4.85h (68% improvement) |
| IAA — FC-4 | `analysis/statistical/` | Fleiss κ = 0.76 |
| IAA — TI-2 | `analysis/statistical/` | Fleiss κ = 0.71 |
| Reliability — TI-3 | `analysis/statistical/` | Cronbach α = 0.84 |

Figures are written to `analysis/figures/` as PDF and PNG.

---

## Data Availability

All data files referenced in `data_dictionary.json` are included in this repository.
Raw data that cannot be released due to confidentiality (full interview transcripts,
signed consent forms) is documented in `data_management_plan.md` and available to
reviewers on request.

See `known_deviations.md` for cases where replication produces approximate rather
than exact matches to paper values.

---

## Troubleshooting

**Import errors**: Ensure the QALIS package is installed (`pip install -e .`)
and the conda environment is active.

**Data file not found**: Run from the repository root directory, not from within
`supplementary/`.

**Slightly different numerical results**: See `known_deviations.md`. Small
differences in floating-point results are expected on different hardware/OS.

**Further help**: Open a GitHub Issue with the error message and system details.
