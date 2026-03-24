# QALIS Instantiation Guide

**Version:** 1.0  
**Paper reference:** §4.1 — Framework Instantiation  
**Estimated time to complete:** 2–4 hours for a single production system

---

## Overview

This guide walks through the four-step process for instantiating QALIS on a new
LLM-integrated software system. Instantiation means tailoring the generic QALIS
framework to your specific system architecture, domain, and risk level — producing
a system-specific metric configuration and monitoring plan.

The four steps are:

1. **Characterise your system** — identify architectural layers and LLM integration points  
2. **Select applicable metrics** — choose which of the 24 QALIS metrics apply  
3. **Configure thresholds** — set or calibrate per-metric pass/fail thresholds  
4. **Establish collection cadences** — decide when and how each metric is measured  

---

## Step 1 — Characterise Your System

Answer each question below. Your answers drive metric selection in Step 2.

### 1.1 Architecture Checklist

| Question | Options | Your answer |
|----------|---------|-------------|
| How is the LLM called? | Direct API / Self-hosted / Fine-tuned | |
| Does the system use retrieval (RAG)? | Yes / No | |
| Does the system produce code? | Yes / No | |
| Is there a user-facing explanation or rationale? | Yes / No | |
| Is the output used to make high-stakes decisions? | Yes / No | |
| Does the system handle PII or regulated data? | Yes / No / HIPAA / GDPR | |
| What is the domain? | Healthcare / Finance / Legal / Customer support / Code / Other | |
| Is there a ground-truth oracle available? | Yes (automated) / Yes (human) / No | |
| Is the system monitored in real-time? | Yes / No / Planned | |

### 1.2 Map to QALIS Layers

Based on your answers, identify which architectural layers are present:

| Layer | Present? | Notes |
|-------|----------|-------|
| **Layer 1 — Input Quality** | ✓/✗ | Present in all RAG systems; also relevant when prompts are template-driven |
| **Layer 2 — Model Behavior** | ✓ | Always present (the LLM component itself) |
| **Layer 3 — Output Quality** | ✓ | Always present (the response delivered to the user or downstream system) |
| **Layer 4 — System Integration Quality** | ✓/✗ | Present when the LLM is called as a service via API; not applicable for offline batch inference |

### 1.3 System Profile Template

Create a YAML system profile in `configs/system_profiles/<your_system_id>.yaml`:

```yaml
system_id: "MY_SYS"
system_name: "My LLM-integrated System"
domain: "customer_support"          # customer_support | code_generation | document_qa |
                                    # medical | legal | financial | general
risk_level: "medium"                # low | medium | high | critical
llm_provider: "openai"              # openai | anthropic | google | self_hosted | other
llm_model: "gpt-4o"
architecture:
  uses_rag: true
  streaming: false
  agentic: false
  code_generation: false
  user_facing: true
  real_time_api: true
data_classification:
  contains_pii: false
  regulated: false                  # HIPAA / GDPR / EU-AI-Act
  regulation: null
team_size: 8
daily_active_users: 2500
```

The four case study profiles (`configs/system_profiles/S1–S4`) serve as reference examples.

---

## Step 2 — Select Applicable Metrics

Use the decision table below. For each metric, check whether the preconditions match
your system profile from Step 1.

### Functional Correctness (FC)

| Metric | Precondition | Include? | Notes |
|--------|-------------|----------|-------|
| **FC-1** Task Accuracy | Ground truth available | ✓ if oracle exists | Use automated eval suite |
| **FC-2** BERTScore F1 | Natural language output | ✓ always | Skip for pure code systems |
| **FC-3** Pass@k | Code generation system | Only if code_generation=true | Requires unit test harness |
| **FC-4** Factual Precision | Factual claims in output | ✓ if factual domain | Requires human annotation panel |

### Robustness (RO)

| Metric | Precondition | Include? | Notes |
|--------|-------------|----------|-------|
| **RO-1** Perturbation Sensitivity | Any system | ✓ always | Use `perturbation_tests/typographical/` |
| **RO-2** Injection Resistance | User-controlled input | ✓ if user_facing=true | Use `red_team/` corpus |
| **RO-3** OOD Detection Rate | User-controlled input | ✓ if user_facing=true | Requires in-distribution centroids |
| **RO-4** Semantic Invariance | Paraphrase equivalence expected | ✓ for QA systems | Use `perturbation_tests/paraphrase/` |
| **RO-5** Adversarial Robustness | High-stakes or regulated | ✓ if risk_level=high | Combined RO-1+RO-2+RO-4 stress test |

### Semantic Faithfulness (SF)

| Metric | Precondition | Include? | Notes |
|--------|-------------|----------|-------|
| **SF-1** Faithfulness NLI | Context/document available | ✓ if uses_rag=true | Requires NLI model |
| **SF-2** Attribution Coverage | Source citation expected | ✓ if RAG + user_facing | Regex or structured output check |
| **SF-3** Hallucination Rate | Factual claims in output | ✓ always | Requires NLI model |

### Safety & Security (SS)

| Metric | Precondition | Include? | Notes |
|--------|-------------|----------|-------|
| **SS-1** Toxicity Rate | User-facing output | ✓ always | Perspective API or local model |
| **SS-2** PII Leakage Rate | Output may contain PII | ✓ if contains_pii=true or regulated | spaCy NER + regex |
| **SS-3** Injection Success Rate | User-controlled input | ✓ if user_facing=true | Red-team corpus |
| **SS-4** Policy Compliance | Domain-specific policies exist | ✓ if regulated or domain-specific | Requires policy ruleset config |

### Transparency & Interpretability (TI)

| Metric | Precondition | Include? | Notes |
|--------|-------------|----------|-------|
| **TI-1** Explanation Coverage | User-facing explanation expected | ✓ if user_facing=true | Structured output check |
| **TI-2** Explanation Faithfulness | Explanations provided | ✓ if TI-1 included | Requires human annotation |
| **TI-3** User Interpretability | Direct user interface | ✓ if user_facing=true | Likert survey instrument |
| **TI-4** Audit Trail Completeness | Audit/compliance required | ✓ if regulated or risk_level≥medium | Log schema validation |

### System Integration Quality (IQ)

| Metric | Precondition | Include? | Notes |
|--------|-------------|----------|-------|
| **IQ-1** API Availability | Real-time API call | ✓ if real_time_api=true | HTTP status monitoring |
| **IQ-2** Response Latency P95 | Real-time API call | ✓ if real_time_api=true | P95 latency SLA tracking |
| **IQ-3** Cost per Query | Token-based billing | ✓ if cost tracked | Provider billing API |
| **IQ-4** Observability Index | Any production system | ✓ always | Audit log completeness check |

### Minimum viable QALIS profile (all systems)

At minimum, every system should collect:
`FC-1, SF-3, RO-2, SS-1, TI-4, IQ-1, IQ-2, IQ-4`

This covers the most critical failure modes (accuracy, hallucination, injection, toxicity,
audit, availability, latency) with fully automated measurement and no human annotation.

---

## Step 3 — Configure Thresholds

### 3.1 Use paper-validated defaults

The file `configs/metrics_thresholds.yaml` contains all 24 default thresholds as reported
in Table 3 of the paper. These thresholds were calibrated from:
- Practitioner interviews (14 industry practitioners across 7 sectors)
- Threshold sensitivity analysis (`experiments/threshold_sensitivity/`)
- ISO 25010 quality targets for mission-critical software

Start with the defaults unless you have domain-specific requirements.

### 3.2 Domain overrides

The threshold file already provides domain overrides for common cases:

```yaml
FC-1:
  threshold: 0.85           # Default
  domain_overrides:
    clinical_decision_support: 0.80   # Harder tasks; human-in-loop compensates
    code_generation: 0.90             # Executable oracle; higher bar justified
```

For your system, add an override block:

```yaml
FC-1:
  domain_overrides:
    <your_domain>: <your_threshold>
```

### 3.3 Calibration from historical data

If you have ≥30 days of production data, calibrate thresholds empirically:

```bash
python experiments/threshold_sensitivity/run_threshold_sweep.py \
  --system-id MY_SYS \
  --metric FC-1 \
  --data-path data/raw/MY_SYS/metric_snapshots/daily_metrics.csv \
  --output experiments/threshold_sensitivity/MY_SYS_sweep.json
```

Set the threshold at the 10th percentile of historical passing observations.
This ensures the threshold reflects achievable performance for your system.

### 3.4 Threshold documentation

Record the rationale for each threshold in your system profile:

```yaml
threshold_rationale:
  FC-1: "0.85 default — no domain override needed for general QA"
  SS-2: "0.0001 — HIPAA compliance; stricter than default 0.001"
  IQ-2: "2000ms — SLA from service contract with enterprise customers"
```

---

## Step 4 — Establish Collection Cadences

### 4.1 Map metrics to cadences

| Cadence | Metrics | Trigger |
|---------|---------|---------|
| **Real-time (5 min)** | SS-1, SS-2, SS-3, IQ-1, IQ-2, IQ-3 | Continuous streaming |
| **Daily** | FC-1, SF-1, SF-2, SF-3, SS-4, TI-1, TI-4 | Scheduled 02:00 UTC |
| **Weekly** | FC-4, RO-1, RO-3, RO-4, RO-5, IQ-4 | Scheduled Monday 03:00 UTC |
| **Per-release** | FC-2, FC-3, RO-2, TI-2, TI-3 | CI/CD gate trigger |
| **Quarterly** | All dimensions (full audit) | Manual or scheduled |

### 4.2 Integration with the toolkit

```python
from toolkit.collectors.qalis_collector import QALISCollector

collector = QALISCollector(
    system_id="MY_SYS",
    domain="customer_support",
    config_path="configs/metrics_thresholds.yaml",
    system_profile_path="configs/system_profiles/MY_SYS.yaml",
)

# Called at inference time (real-time metrics)
result = collector.evaluate_interaction(
    query="...",
    response="...",
    context=retrieved_docs,       # None if not RAG
    ground_truth=reference,       # None if no oracle
    latency_ms=843,
    api_status=200,
)

# Called nightly (daily/weekly metrics)
daily_result = collector.run_daily_batch(
    eval_set_path="data/processed/eval_sets/fc1_regression_suite.csv"
)
```

### 4.3 CI/CD integration

Add quality gates to your deployment pipeline:

```yaml
# .github/workflows/your_deployment.yml
jobs:
  quality-gate:
    uses: ./.github/workflows/quality_gate.yml
    with:
      system_id: MY_SYS
      trigger: model_version_update
      version: ${{ github.sha }}
    secrets: inherit
```

See `.github/workflows/quality_gate.yml` for the full reusable workflow.

---

## Worked Example: Instantiating QALIS for a Legal Document QA System

**System:** RAG-based legal document Q&A assistant, answering questions from uploaded
contracts. High-stakes domain (legal advice adjacent), user-facing, GDPR-regulated.

**Step 1 result:**
```yaml
system_id: "LEGAL_QA"
domain: "legal"
risk_level: "high"
uses_rag: true
contains_pii: true
regulated: true
regulation: "GDPR"
```

**Step 2 result — selected metrics:**
All metrics applicable; FC-3 excluded (no code generation).

**Step 3 result — threshold overrides:**
```yaml
FC-1: 0.88     # Higher bar for legal accuracy
SF-3: 0.003    # Stricter: legal hallucinations are high-risk
SS-2: 0.0001   # GDPR requirement
TI-2: 0.80     # Explanations must be highly faithful
TI-4: 1.0      # Full audit trail required for GDPR
```

**Step 4 result:**
Real-time: SS-1, SS-2, SS-3, IQ-1, IQ-2 (injection and PII checked on every query)  
Daily: FC-1, SF-3, TI-4 (accuracy, hallucination, audit completeness)  
Per-release: RO-2 (injection resistance re-tested after any prompt template change)

---

## Reference: Case Study Instantiation Summaries

| System | Metrics used | Key threshold adjustments | Paper section |
|--------|-------------|--------------------------|---------------|
| S1 Customer Support | 22/24 (IQ-3 excluded) | FC-1=0.85, SS-1=0.005 | §4.2 |
| S2 Code Assistant | 23/24 (TI-3 excluded) | FC-3=0.90, FC-1=0.88 | §4.3 |
| S3 Document QA | 24/24 | SF-1=0.80, SF-3=0.015 | §4.4 |
| S4 Medical Triage | 23/24 (IQ-3 excluded) | FC-1=0.80, SS-2=0.0001 | §4.5 |

Full configurations: `configs/system_profiles/S1–S4_*.yaml`  
Full annotated results: `supplementary/annotated_case_studies/`

---

*Questions? Open a GitHub Issue tagged `instantiation-help`.*
