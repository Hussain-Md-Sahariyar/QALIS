# QALIS User Guide

## Overview

This guide explains how to use the QALIS framework to assess the quality of your
LLM-integrated software system. It covers:

1. [Core Concepts](#1-core-concepts)
2. [Installation](#2-installation)
3. [Framework Instantiation](#3-framework-instantiation)
4. [Collecting Metrics](#4-collecting-metrics)
5. [Interpreting Results](#5-interpreting-results)
6. [Working with the Study Data](#6-working-with-the-study-data)
7. [Reproducing Paper Results](#7-reproducing-paper-results)

---

## 1. Core Concepts

### The Four-Layer Architecture

QALIS models quality across four architectural layers, each targeting a distinct
failure surface in LLM-integrated systems:

```
┌─────────────────────────────────────────────┐
│  Layer 4 — System Integration Quality (IQ)  │
│  API reliability · latency · cost · observ. │
├─────────────────────────────────────────────┤
│  Layer 3 — Output Quality                   │
│  SF: Faithfulness · hallucination           │
│  SS: Toxicity · PII · injection · policy    │
│  TI: Explanation · interpretability · audit  │
├─────────────────────────────────────────────┤
│  Layer 2 — Model Behaviour                  │
│  FC: Task accuracy · factual precision      │
│  RO: Perturbation · injection · OOD         │
├─────────────────────────────────────────────┤
│  Layer 1 — Input Quality                    │
│  Prompt engineering · context completeness  │
└─────────────────────────────────────────────┘
```

### Six Quality Dimensions

| ID | Dimension | Key Question |
|----|-----------|-------------|
| FC | Functional Correctness | Does the system produce accurate, complete outputs? |
| RO | Robustness | Does quality hold under adversarial or atypical inputs? |
| SF | Semantic Faithfulness | Are outputs grounded in provided context? |
| SS | Safety & Security | Is the system safe and injection-resistant? |
| TI | Transparency & Interpretability | Can users understand and trust the system's reasoning? |
| IQ | System Integration Quality | Is the infrastructure reliable, fast, and observable? |

### 24 Metrics

Each dimension is operationalized by 3–5 metrics. See `framework/metrics/metrics_catalogue.json`
for formulas, collection methods, and thresholds. Key metrics by dimension:

- **FC**: FC-1 Task Accuracy (≥0.85), FC-4 Factual Precision (≥0.80)
- **RO**: RO-2 Injection Resistance (≥0.97), RO-4 Semantic Invariance (≥0.85)
- **SF**: SF-1 Faithfulness Score (≥0.88), SF-3 Hallucination Rate (≤2.0/1K tokens)
- **SS**: SS-1 Toxicity Rate (≤0.005), SS-2 PII Leakage (≤0.001)
- **TI**: TI-1 Explanation Coverage (≥0.70), TI-4 Audit Trail (≥0.99)
- **IQ**: IQ-1 API Availability (≥0.999), IQ-2 P95 Latency (≤2500ms)

---

## 2. Installation

### Requirements

- Python 3.10+
- CUDA-capable GPU recommended (for NLI classifier); CPU fallback available

```bash
# Clone the repository
git clone https://github.com/[anonymised]/qalis-quatic2025.git
cd qalis-quatic2025

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "from toolkit.collectors.qalis_collector import QALISCollector; print('OK')"
```

### Key Dependencies

| Package | Purpose |
|---------|---------|
| `transformers` | DeBERTa-NLI for SF metrics |
| `sentence-transformers` | Embedding generation for RO metrics |
| `spacy` + `en_core_web_trf` | PII/NER detection (SS-2) |
| `scipy`, `statsmodels` | Statistical analysis |
| `pandas`, `numpy` | Data processing |

---

## 3. Framework Instantiation

Before collecting metrics, QALIS must be instantiated for your specific system.
This involves three steps:

### Step 1 — Create a System Profile

Copy and edit a template from `configs/system_profiles/`:

```yaml
# configs/system_profiles/my_system.yaml
system:
  id: MY_SYS
  name: "My LLM Application"
  domain: customer_support        # or: code_generation, document_intelligence,
                                  #     clinical_decision_support, other
  risk_level: medium              # low | medium | high

infrastructure:
  llm_provider: openai
  llm_model: "gpt-4o-2024-08-06"
  rag_enabled: true
  streaming_enabled: false

metric_overrides:
  IQ-2:
    threshold: 2000               # Tighten latency SLA if needed
```

### Step 2 — Calibrate Thresholds

The default thresholds in `configs/metrics_thresholds.yaml` reflect study averages.
For production use, calibrate during a 2-week onboarding period:

```python
from toolkit.collectors.qalis_collector import QALISCollector

collector = QALISCollector(system_id="MY_SYS")

# Run on a representative sample of recent production traffic
calibration_results = collector.calibrate(
    sample_logs="path/to/recent_logs.jsonl",
    n_samples=500
)
print(calibration_results.suggested_thresholds)
```

### Step 3 — Validate Instrumentation

```python
# Check that all applicable metrics can be collected
report = collector.validate_instrumentation()
print(f"IQ-4 Observability Index: {report.iq4_score:.2f}")
# Target: ≥ 0.90 before going live
```

---

## 4. Collecting Metrics

### Single Evaluation

```python
from toolkit.collectors.qalis_collector import QALISCollector

collector = QALISCollector(
    system_id="MY_SYS",
    config_path="configs/qalis_config.yaml"
)

result = collector.evaluate(
    query="What is your cancellation policy?",
    response="You can cancel anytime by visiting Account > Subscriptions.",
    context="Cancellation: customers may cancel at any time via Account settings.",
    metadata={"session_id": "sess-001", "latency_ms": 843}
)

print(f"Composite:  {result.composite_score:.2f}")
print(f"SF-1:       {result.dimension_scores['SF']:.3f}")
print(f"SF-3:       {result.metrics['SF-3']:.4f} hallucinations/1K tokens")
print(f"Violations: {result.threshold_violations}")
```

### Batch Evaluation

```python
import pandas as pd

logs = pd.read_json("data/raw/MY_SYS/query_logs/query_response_log.jsonl", lines=True)

results = collector.evaluate_batch(
    queries=logs["query"].tolist(),
    responses=logs["response"].tolist(),
    contexts=logs["context"].tolist(),    # None for non-RAG systems
    n_workers=4
)

summary = results.summary()
print(summary.dimension_means)
```

### Streaming (Realtime) Collection

```python
from toolkit.collectors.qalis_collector import QALISStreamCollector

stream = QALISStreamCollector(system_id="MY_SYS", flush_interval_seconds=300)

# In your application's response handler:
@app.after_request
def collect_qalis(response):
    stream.record(
        query=request.json["query"],
        response=response.json["answer"],
        context=request.json.get("context"),
        latency_ms=response.headers.get("X-Latency-Ms")
    )
    return response
```

---

## 5. Interpreting Results

### Score Scale

All QALIS dimension scores are normalised to a 0–10 scale:

| Score Range | Interpretation |
|-------------|---------------|
| 9.0 – 10.0 | Excellent — exceeds all thresholds with margin |
| 7.5 – 8.9 | Good — all thresholds met; minor improvement opportunities |
| 6.0 – 7.4 | Acceptable — most thresholds met; targeted improvements needed |
| 4.0 – 5.9 | Concerning — multiple threshold violations; urgent attention required |
| < 4.0 | Critical — systematic quality failure |

### Threshold Violations

Violations are ranked by severity:

```python
for v in result.threshold_violations:
    print(f"[{v.severity.upper()}] {v.metric_id}: {v.value:.4f} {v.operator} {v.threshold}")
    print(f"  → {v.recommended_action}")
```

### Cross-Layer Causal Tracing

When a violation occurs, QALIS traces likely root causes across layers:

```
SF-3 VIOLATION (hallucination rate 3.2 > 2.0)
├── Check SF-1 (faithfulness score): 0.71 — BELOW THRESHOLD
│   └── Investigate: NLI analysis log for contradicted claims
├── Check RO-4 (semantic invariance): 0.79 — BELOW THRESHOLD  ← r=0.61 proxy
│   └── Run paraphrase consistency test suite
└── Escalation path: Context retrieval → Prompt template → Model update
```

### Transparency (TI) — The Most Actionable Gap

Across all four study systems, TI was the lowest-scoring dimension (mean 7.05, σ=1.35).
Practitioners in 11 of 14 interviews identified explanation quality as underserved.
If your TI score is below 7.5, prioritise:

1. **TI-1**: Add chain-of-thought, source citations, or confidence indicators to responses
2. **TI-4**: Ensure audit trail completeness (all 13 required fields logged)
3. **TI-2**: Conduct quarterly human evaluation of explanation faithfulness

---

## 6. Working with the Study Data

### Loading Metric Snapshots

```python
import pandas as pd

# Daily metrics for S1
daily = pd.read_csv("data/raw/S1_Customer_Support_Chatbot/metric_snapshots/daily_metrics.csv")
daily["date"] = pd.to_datetime(daily["date"])
print(daily[["date","FC-1","SF-3","TI-1"]].tail(10))

# Realtime metrics (compressed)
realtime = pd.read_csv(
    "data/raw/S1_Customer_Support_Chatbot/metric_snapshots/realtime_metrics.csv.gz",
    compression="gzip"
)
```

### Loading Embeddings

```python
import numpy as np

query_emb = np.load(
    "data/raw/S1_Customer_Support_Chatbot/embeddings/query_embeddings.npy"
)  # shape: (50000, 512), dtype: float32

# Cosine similarity between query and response embeddings
response_emb = np.load(
    "data/raw/S1_Customer_Support_Chatbot/embeddings/response_embeddings.npy"
)
from sklearn.metrics.pairwise import cosine_similarity
sims = cosine_similarity(query_emb[:100], response_emb[:100])
```

### Loading Annotation Data

```python
import pandas as pd

# FC-4 annotations (800 claims, Fleiss κ=0.76)
fc4 = pd.read_csv("data/annotations/FC4_factual_precision/fc4_all_systems_combined.csv")
print(fc4["majority_judgment"].value_counts())
# CORRECT         612
# UNVERIFIABLE     96
# INCORRECT        92

# TI-3 user ratings (1200 responses, S1/S3/S4 only)
ti3 = pd.read_csv("data/annotations/TI3_user_interpretability/ti3_all_systems_combined.csv")
print(ti3.groupby("system_id")["composite_score"].mean())
```

---

## 7. Reproducing Paper Results

```bash
# Run all analyses and generate Figures 3–6
python analysis/replicate_all_results.py

# Individual analyses
python analysis/rq1/dimension_coverage_analysis.py
python analysis/rq2/metric_correlation_analysis.py
python analysis/rq3/comparative_effectiveness_analysis.py

# Generate specific figure
python analysis/generate_all_figures.py --fig 3

# Full statistical report
python analysis/statistical/mixed_effects_models.py
```

Expected outputs align with paper findings:
- Table 4 composite scores: S1=7.23, S2=7.68, S3=8.02, S4=8.15
- Figure 4 key correlations: SF-3↔RO-4 r=0.61, IQ-2↔IQ-1 r=0.74
- Figure 6: 81% hallucination reduction, 77% integration error reduction by Month 3
- All RQ3 Wilcoxon tests: p < 0.001 (Bonferroni-corrected α = 0.000556)
