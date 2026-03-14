# QALIS Case Study Research Protocol

**Version**: 1.0  
**Approved**: September 2024  
**IRB reference**: QUATIC-2025-IRB-Annex-B  
**Paper reference**: §3 — Research Methodology  

---

## 1. Research Questions

This study addresses three research questions:

**RQ1** — *What quality dimensions are relevant and measurable for LLM-integrated
software systems in production?*

**RQ2** — *How can each quality dimension be operationalised through measurable
metrics in deployed LLM systems?*

**RQ3** — *How does QALIS compare to existing quality assessment approaches in
detecting quality degradations in production LLM systems?*

---

## 2. Research Design

### 2.1 Strategy: Multiple-Case Study

Following Yin (2014), a multiple-case embedded design was selected. Case studies are
appropriate here because (a) the phenomenon (quality assessment of production LLM
systems) is contemporary and context-dependent; (b) researchers have no control over
the systems under study; and (c) the research questions are explanatory and comparative.

**Replication logic**: Each case system (S1–S4) is treated as a replication unit. The
four cases span four domains and LLM providers, providing both literal replication
(similar domains expect similar findings) and theoretical replication (diverse domains
allow boundary conditions to emerge).

### 2.2 Unit of Analysis

The primary unit of analysis is a **single LLM interaction** (one query/response pair),
evaluated on all 24 QALIS metrics. Secondary units are the system-month (for
longitudinal analysis) and the practitioner (for interview analysis).

### 2.3 Case Selection

Cases were selected using theoretical sampling to maximise domain and LLM diversity:

| Criterion | S1 | S2 | S3 | S4 |
|-----------|----|----|----|----|
| Domain | Customer Support | Code Generation | Document QA | Medical Triage |
| LLM provider | OpenAI | Anthropic | Google | Meta (self-hosted) |
| Risk level | Medium | Medium | Medium | High |
| Interaction volume | 50K+ / month | 50K+ / month | 50K+ / month | 20K+ / month |
| Regulatory context | None | None | GDPR | HIPAA / EU AI Act |
| Context window use | Moderate | Moderate | High (RAG) | Moderate |

---

## 3. Data Collection

### 3.1 Quantitative Data: Metric Collection

**Collection period**: 1 October – 31 December 2024 (92 days per system)

**Sample size**: 850 observations per system (3,400 total), stratified as:
- 100 per system per month × 3 months = 300 (monthly stratified)
- 50 per system per month from real-time monitoring logs = 550 top-up

**Stratification variables**:
- Calendar week (to capture temporal trends for RQ3)
- Interaction type (query complexity tier: simple / moderate / complex)
- Time of day (business hours / off-hours, to capture load variation)

**Metric collection cadence** (from `configs/qalis_config.yaml`):
- Real-time (5-min): IQ-1, IQ-2, SS-1, SS-2, SS-3
- Daily batch: FC-1, SF-1, SF-2, SF-3, SS-4, TI-1, TI-4
- Weekly batch: FC-4, RO-1, RO-3, RO-4, RO-5, IQ-4
- On-event: RO-2 (red-team suite), TI-2 (annotation panel), TI-3 (user survey)

**Baseline collection**: ISO 25010, HELM, and MLflow metrics were collected in parallel
using identical sampling frames to support RQ3 comparative analysis.

### 3.2 Qualitative Data: Practitioner Interviews

**Purpose**: Validate QALIS metric relevance; calibrate thresholds; elicit practitioner
concerns about LLM quality that are not captured by existing frameworks.

**Protocol**: Semi-structured (see `survey_instruments/practitioner_interview_guide.txt`)

**Sampling**: Purposive sampling. Target: practitioners currently responsible for
production LLM systems across diverse sectors.

**Recruitment**: Via professional networks (LinkedIn), conference contacts (NeurIPS 2023,
ICSE 2024), and research team industry partners.

**Conduct**: Audio-recorded video calls with verbal consent. Verbatim transcription with
minor disfluency removal. Anonymisation before analysis (org, product, vendor names
replaced with role-descriptive codes).

**Analysis method**: Framework method (Ritchie & Spencer, 1994) applied by two
independent analysts. Codebook in `interviews/codebook/`. Cohen's κ = 0.81.

### 3.3 Perturbation and Red-Team Data

- **RO-1/RO-4**: 5,000 typographical perturbations, 4,000 paraphrase pairs
  (generated automatically per `configs/perturbation_config.yaml`)
- **RO-2/SS-3**: 2,850 prompt injection attempts across 9 categories, 54 patterns
  (red-team suite per `configs/red_team_config.yaml`)
- **RO-3**: 3,000 OOD detection test cases across 10 categories

### 3.4 Human Annotation

Two metrics required human judgment by three independent annotators:

| Metric | Items | Annotators | IAA | Target |
|--------|-------|------------|-----|--------|
| FC-4 Factual Precision | 800 | 3 | Fleiss κ = 0.76 | κ ≥ 0.70 |
| TI-2 Explanation Faithfulness | 500 | 1st 2nd 3rd | Fleiss κ = 0.71 | κ ≥ 0.70 |
| TI-3 User Interpretability | 14 participants × 4 items | N/A | Cronbach α = 0.84 | α ≥ 0.70 |

See `survey_instruments/annotator_training_guide.md` and rubrics.

---

## 4. Data Analysis

### 4.1 RQ1 Analysis

- Per-system quality profiles (radar charts, Figure 3)
- Inter-dimension Pearson correlations (verify independence: median |r| = 0.31)
- Dimension activation across systems (all 6 active in ≥ 3 systems)

### 4.2 RQ2 Analysis

- Per-metric descriptive statistics across 3,400 observations
- Pearson and Kendall correlation matrix for 8 key metrics (Figure 4)
- IAA verification for human-judged metrics (FC-4, TI-2, TI-3)
- Cross-layer causal analysis

### 4.3 RQ3 Analysis

- Wilcoxon signed-rank tests (18 comparisons: 6 dimensions × 3 baselines)
- Bonferroni correction: α_corrected = 0.01 / 18 = 0.000556
- Effect size: r = Z / √N
- Detection lag comparison (incident log analysis, n = 42 incidents)
- Monthly resistance trend (longitudinal, 3 time points)

### 4.4 Mixed-Effects Models (Longitudinal)

Linear mixed-effects models with system as random effect, time as fixed effect.
Implemented via `statsmodels` MixedLM. Approximated by per-approach OLS in
`analysis/statistical/mixed_effects_models.py` for reproducibility without
proprietary data.

---

## 5. Validity Procedures

### 5.1 Construct Validity

- Multiple sources of evidence for each metric (automated + human annotation)
- Member checking: interview findings validated with 3 participants post-analysis
- Peer review: codebook reviewed by a second researcher before coding

### 5.2 Internal Validity

- Rival explanations considered for correlation findings (e.g. SF-3 ↔ RO-4)
- Time-series analysis controls for temporal confounds
- Baseline collection under identical conditions to QALIS

### 5.3 External Validity

- Four diverse domains and LLM providers
- Practitioner sample spanning 6 sectors, 3 continents
- Explicit documentation of boundary conditions (§7 threats to validity)

### 5.4 Reliability

- Automated metrics: deterministic (seeded RNG where applicable)
- Human annotation: IAA targets met (κ ≥ 0.70 for FC-4, TI-2)
- Analysis scripts in `analysis/` produce identical results on re-run

---

## 6. Timeline

| Phase | Period | Activities |
|-------|--------|------------|
| Protocol design | Aug–Sep 2024 | Research design, instrument development, IRB submission |
| Pilot | Sep 2024 | Pilot metric collection (2 weeks), annotator training |
| Data collection | Oct–Dec 2024 | 92-day metric collection period; interviews Nov–Dec |
| Analysis | Jan 2025 | Statistical analysis, qualitative coding, figure generation |
| Write-up | Jan–Feb 2025 | Paper drafting, internal review, submission |

---

## 7. Ethical Considerations

- IRB approval obtained (QUATIC-2025-IRB-Annex-B) before data collection began
- All interview participants provided informed written consent
- Case system operators provided data use agreements
- All personal data removed before archiving; transcripts anonymised
- Red-team payloads stored in obfuscated/parameterised form; not published verbatim
- See `data_management_plan.md` and `irb_approval_summary.md`

---

## References

- Yin, R.K. (2014). *Case Study Research: Design and Methods* (5th ed.). SAGE.
- Ritchie, J., & Spencer, L. (1994). Qualitative data analysis for applied policy research.
  In A. Bryman & R. Burgess (Eds.), *Analysing Qualitative Data* (pp. 173–194). Routledge.
- Wohlin, C., et al. (2012). *Experimentation in Software Engineering*. Springer.
