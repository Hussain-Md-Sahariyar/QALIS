# QALIS: Quality Assessment Framework for LLM-Integrated Software Systems

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Observations: 3,400](https://img.shields.io/badge/Observations-3%2C400-green)](data/processed/)
[![Metrics: 24](https://img.shields.io/badge/QALIS%20Metrics-24-orange)](framework/metrics/)
[![Systems: 4](https://img.shields.io/badge/Case%20Systems-4-purple)](data/raw/)
[![Interviews: 14](https://img.shields.io/badge/Practitioner%20Interviews-14-red)](interviews/)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](pyproject.toml)

---

## What is QALIS?

**QALIS** (Quality Assessment for LLM-Integrated Software Systems) is an open-source, empirically validated quality framework for production software systems that integrate Large Language Model (LLM) components.

It bridges the gap between:
- **Software quality engineering** (ISO 25010, reliability, maintainability) — which lacks LLM-specific metrics
- **LLM evaluation** (HELM, BIG-bench) — which treats the model in isolation, ignoring system context

QALIS provides a **four-layer architecture** with **24 fully operationalized metrics** across **6 quality dimensions**, validated across 4 industrial systems over a 3-month study.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Detailed Setup](#detailed-setup)
3. [Repository Structure](#repository-structure)
4. [Usage Guide](#usage-guide)
   - [Instrumenting Your System](#instrumenting-your-system)
   - [Running the Analysis Scripts](#running-the-analysis-scripts)
   - [CI/CD Quality Gates](#cicd-quality-gates)
   - [Monitoring Dashboard](#monitoring-dashboard)
5. [QALIS Framework](#qalis-framework)
6. [Case Study Systems](#case-study-systems)
7. [Key Empirical Results](#key-empirical-results)
8. [Replication](#replication)
9. [License](#license)

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/Hussain-Md-Sahariyar/QALIS.git
cd QALIS
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

# Reproduce all results
python supplementary/replication_package/replicate_all_results.py

# Or run individual analyses
python analysis/rq1/dimension_coverage_analysis.py
python analysis/rq2/metric_correlation_analysis.py
python analysis/rq3/comparative_effectiveness_analysis.py
```

---

## Detailed Setup

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.10 | 3.11 |
| RAM | 8 GB | 32 GB |
| GPU | — | NVIDIA A10G (24 GB VRAM) |
| Disk | 5 GB | 20 GB |
| OS | Ubuntu 22.04 / macOS 13 / Windows 11 | Ubuntu 22.04 |

GPU is optional but strongly recommended for the NLI classifier (SF dimension). Without a GPU, NLI inference falls back to CPU and is ~16× slower (5 vs 80 evaluations/second).

### Step-by-step Installation

#### 1. Clone the repository

```bash
git clone https://github.com/Hussain-Md-Sahariyar/QALIS.git
cd QALIS
```

#### 2. Create and activate a virtual environment

```bash
# Linux / macOS
python -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

Alternatively, use the provided conda environment:

```bash
conda env create -f supplementary/replication_package/environment.yml
conda activate qalis
```

#### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e . # Installs src/qalis as an editable package
```

#### 4. Download NLP models (required for SF and SS dimensions)

```bash
# spaCy NER model (SS-2 PII detection)
python -m spacy download en_core_web_trf # Production (transformer-based)
python -m spacy download en_core_web_sm # Lightweight alternative for CI

# DeBERTa NLI model (SF-1, SF-3 hallucination) — downloads on first use
# Pre-download to avoid cold start:
python -c "
from transformers import AutoTokenizer, AutoModelForSequenceClassification
m = 'cross-encoder/nli-deberta-v3-large'
AutoTokenizer.from_pretrained(m)
AutoModelForSequenceClassification.from_pretrained(m)
print('NLI model ready.')
"

# Sentence transformer (RO-3 OOD detection) — downloads on first use
python -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
print('Sentence transformer ready.')
"
```

#### 5. Configure environment variables

Create a `.env` file in the project root (never commit this file):

```bash
# Required for SS-1 toxicity (Perspective API)
PERSPECTIVE_API_KEY=your_api_key_here

# Required only if using OpenAI LLM in your own system
OPENAI_API_KEY=your_openai_key_here

# Optional: Slack CI/CD alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Optional: set default system ID
QALIS_SYSTEM_ID=MY_SYS
```

Load in Python:
```python
from dotenv import load_dotenv
load_dotenv()
```

Or export directly:
```bash
export PERSPECTIVE_API_KEY=your_key_here
```

#### 6. Verify installation

```bash
python -c "
from src.qalis.framework import QALISFramework
from toolkit.collectors.qalis_collector import QALISCollector
print('QALIS installation verified.')
print(f'Framework version: {QALISFramework.__version__}')
"
```

#### 7. Run the test suite

```bash
pytest tests/ -m "not slow and not integration" -v
```

---

## Repository Structure

```
QALIS/
│
├── framework/                    
│   ├── qalis_framework_spec.md  
│   ├── layers/                  
│   ├── metrics/metrics_catalogue.json 
│   └── schemas/                  
│
├── src/qalis/                    
│   ├── framework.py              
│   ├── result.py              
│   ├── metrics/                 
│   ├── collectors/               
│   ├── dashboard/               
│   ├── analysis/               
│   └── utils/                   
│
├── toolkit/                    
│   ├── collectors/qalis_collector.py   
│   ├── classifiers/            
│   ├── ci_gate/quality_gate.py  
│   ├── ci_cd_integration/       
│   ├── exporters/               
│   ├── integrations/           
│   └── dashboard_templates/   
│
├── configs/                   
│   ├── metrics_thresholds.yaml  
│   ├── nli_classifier_config.yaml        
│   ├── classifier_config.yaml  
│   ├── perturbation_config.yaml 
│   ├── ci_cd_config.yaml      
│   ├── monitoring_config.yaml  
│   └── system_profiles/        
│
├── data/
│   ├── annotations/            
│   ├── perturbation_tests/      
│   ├── processed/             
│   │   ├── correlations/       
│   │   ├── eval_sets/           
│   │   └── data_dictionary.json  
│   └── raw/                     
│       └── S{1-4}_*/          
│
├── analysis/                    
│   ├── rq1/dimension_coverage_analysis.py     
│   ├── rq2/metric_correlation_analysis.py     
│   ├── rq3/comparative_effectiveness_analysis.py 
│   ├── statistical/mixed_effects_models.py   
│   └── generate_all_figures.py               
│
├── perturbation_tests/         
│   ├── typographical/          
│   ├── paraphrase/          
│   ├── ood_detection/          
│   └── prompt_injection/       
│
├── red_team/                   
│   ├── run_red_team.py         
│   ├── prompts/                 
│   ├── patterns/              
│   └── results/               
│
├── baselines/                
│
├── experiments/                
│   ├── rq1_dimension_coverage/ 
│   ├── rq2_metric_operationalization/  
│   ├── rq3_comparative_effectiveness/  
│   ├── ablations/              
│   └── threshold_sensitivity/  
│
├── interviews/                 
│   ├── codebook/               
│   └── thematic_analysis/       
│
├── supplementary/
│   ├── annotated_case_studies/ 
│   ├── replication_package/    
│   │   ├── instantiation_guide.md 
│   │   ├── replicate_all_results.py
│   │   ├── replication_checklist.md
│   │   └── known_deviations.md
│   ├── case_study_protocol/    
│   └── survey_instruments/     
│
├── notebooks/                 
├── tests/                      
├── .github/workflows/           
├── docs/                      
├── pyproject.toml
└── requirements.txt
```

---

## Usage Guide

### Instrumenting Your System

The primary entry point is `QALISCollector` in `toolkit/collectors/qalis_collector.py`.

#### Basic single-interaction evaluation

```python
from toolkit.collectors.qalis_collector import QALISCollector

# Initialise once 
collector = QALISCollector(
    system_id="my-chatbot",
    domain="customer_support",         
    config_path="configs/metrics_thresholds.yaml",
    system_profile_path="configs/system_profiles/S1_customer_support.yaml",
)

# Call at inference time for each interaction
result = collector.evaluate_interaction(
    query="What is your refund policy?",
    response="We offer 30-day refunds on all items in original condition...",
    context=retrieved_chunks, # list[str] from RAG; None if no retrieval
    ground_truth=reference_answer, # str or None if no oracle
    latency_ms=843.0,
    api_status_code=200,
)

# Access results
print(result.summary_report())
print(f"Composite score: {result.composite_score:.2f}")
print(f"Violations: {result.violations}")

# Export to MLflow
from toolkit.exporters.mlflow_exporter import MLflowExporter
exporter = MLflowExporter(tracking_uri="http://localhost:5000")
exporter.log_result(result)
```

#### LangChain integration

```python
from toolkit.integrations.langchain_callback import QALISCallbackHandler

handler = QALISCallbackHandler(
    system_id="my-chain",
    collector_config="configs/metrics_thresholds.yaml",
)

# Attach to any LangChain chain/agent
chain = your_rag_chain.with_config(callbacks=[handler])
response = chain.invoke({"question": "..."})
# QALIS metrics are collected automatically on each chain run
```

#### Batch evaluation

```python
from src.qalis.collectors.batch_collector import QALISBatchCollector

batch = QALISBatchCollector(system_id="my-system", config_path="configs/metrics_thresholds.yaml")
results = batch.evaluate_dataset(
    dataset_path="data/processed/eval_sets/fc1_regression_suite.csv",
    n_workers=4,
)
batch.export_summary(results, output_path="reports/batch_results.json")
```

#### Streaming / real-time collection

```python
from src.qalis.collectors.streaming_collector import QALISStreamCollector

stream_collector = QALISStreamCollector(
    system_id="my-system",
    buffer_size=100, # Flush to storage every 100 interactions
    flush_interval_seconds=300, # Or every 5 minutes
)
# Runs as background thread — attach to your API middleware
stream_collector.start()
```

---

### Adapting QALIS to a New System (Instantiation)

Follow the four-step process in the instantiation guide:

```
supplementary/replication_package/instantiation_guide.md
```

**Summary of the four steps:**

1. **Characterise your system** — fill in the system profile template  
   (`configs/system_profiles/` → copy an existing profile as starting point)

2. **Select applicable metrics** — use the decision table in the guide  
   (not all 24 metrics apply to every system; e.g. FC-3 Pass@k only for code generation)

3. **Configure thresholds** — edit `configs/metrics_thresholds.yaml`  
   (use `run_threshold_sweep.py` to calibrate from your data)

4. **Establish collection cadences** — map metrics to real-time / daily / weekly / per-release  
   (copy `configs/monitoring_config.yaml` and adjust for your infrastructure)

---

### Running the Analysis Scripts

All scripts are self-contained and reproducible. Run them from the repository root.

#### Reproduce all paper results

```bash
python supplementary/replication_package/replicate_all_results.py
```

#### Threshold sensitivity analysis

```bash
python experiments/threshold_sensitivity/run_threshold_sweep.py \
  --metric SF-3 \
  --system-id S1 \
  --output experiments/threshold_sensitivity/SF3_sweep_S1.json
```

#### Ablation studies

```bash
python experiments/ablations/run_ablations.py \
  --experiment all \
  --output experiments/ablations/results/
```

---

### CI/CD Quality Gates

QALIS includes a ready-to-use GitHub Actions pipeline that blocks releases when quality degrades below defined thresholds.

#### Manual quality gate run

```bash
python -m toolkit.ci_cd_integration.github_actions \
  --system-id MY_SYS \
  --config-path configs/ci_cd_config.yaml \
  --compare-to last_stable_release \
  --output-file reports/gate_result.json \
  --verbose
```

#### Python API for deployment hooks

```python
from toolkit.ci_cd_integration.deployment_hooks import DeploymentHooks, QALISGateFailure

hooks = DeploymentHooks(
    system_id="MY_SYS",
    config_path="configs/ci_cd_config.yaml",
    compare_to="last_stable_release",
    trigger="model_version_update",
    version="v2.1.0",
)

try:
    hooks.pre_deploy(eval_sets=["fc1_regression_suite", "sf3_regression_suite"])
    # ... your deployment steps ...
    hooks.post_deploy(tag="last_stable_release") # Save as new stable baseline
except QALISGateFailure as e:
    print(f"Deployment blocked: {e.failures}")
    hooks.on_deploy_failure(reason=str(e))
    raise
```

---

### Monitoring Dashboard

#### Start the FastAPI dashboard

```bash
# Development
uvicorn src.qalis.dashboard.app:app --reload --port 8080

# Production
uvicorn src.qalis.dashboard.app:app --workers 4 --port 8080
```

Available endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scores/{system_id}` | GET | Latest dimension + composite scores |
| `/violations` | GET | All active threshold violations |
| `/history/{system_id}` | GET | Time-series of composite scores |
| `/radar/{system_id}` | GET | Dimension scores for radar chart rendering |
| `/ingest` | POST | Ingest a QALISResult from a collector |
| `/metrics` | GET | Prometheus scrape endpoint |
| `/health` | GET | Service health check |

#### Grafana dashboard

1. Start the dashboard API (above)
2. Configure Prometheus to scrape `http://localhost:8080/metrics`
3. Import `toolkit/dashboard_templates/grafana_qalis_overview.json` into Grafana
4. Select your system from the `system_id` dropdown

#### HTML report

```bash
# Generate a standalone HTML quality report
python -c "
from toolkit.ci_gate.quality_gate import QALISQualityGate
import json

gate = QALISQualityGate('MY_SYS', 'configs/ci_cd_config.yaml')
result = gate.run()
result.export_html('reports/qalis_report.html', template='toolkit/dashboard_templates/qalis_html_report_template.html')
"
# Open reports/qalis_report.html in any browser
```

---

## QALIS Framework

QALIS organizes quality concerns across a **four-layer architecture** mirroring the structure of a production LLM-integrated system:

| Layer | Scope | Key dimensions |
|-------|-------|---------------|
| **Layer 1** Input Quality | Signals entering the LLM | Prompt engineering, context completeness, data integrity |
| **Layer 2** Model Behavior | Intrinsic LLM quality | FC (Functional Correctness), RO (Robustness) |
| **Layer 3** Output Quality | Response as received by users | SF (Semantic Faithfulness), SS (Safety & Security), TI (Transparency) |
| **Layer 4** System Integration | LLM-host system boundary | IQ (System Integration Quality) |

### Quality Dimensions and Metrics

| # | Abbrev | Dimension | Metrics | Key Failure Mode | Mean Score |
|---|--------|-----------|---------|-----------------|------------|
| 1 | **FC** | Functional Correctness | FC-1 to FC-4 | Incorrect task completion | 8.00 |
| 2 | **RO** | Robustness | RO-1 to RO-5 | Behavioral degradation under perturbation | 7.28 |
| 3 | **SF** | Semantic Faithfulness | SF-1 to SF-3 | Hallucination, unsupported claims | 8.28 |
| 4 | **SS** | Safety & Security | SS-1 to SS-4 | Toxicity, PII leakage, prompt injection | 8.33 |
| 5 | **TI** | Transparency & Interpretability | TI-1 to TI-4 | Opaque reasoning, poor explanation quality | 7.05 ⚠️ |
| 6 | **IQ** | System Integration Quality | IQ-1 to IQ-4 | API failures, latency SLA breaches | 7.70 |

> ⚠️ **TI (Transparency)** was the lowest-scoring and highest-variance dimension across all four systems — identified as the most critical current quality gap.

Full metric specifications: `framework/metrics/metrics_catalogue.json`  
Threshold table: `configs/metrics_thresholds.yaml`  
Instantiation guide: `supplementary/replication_package/instantiation_guide.md`

---

## Case Study Systems

| ID | Domain | LLM | Architecture | DAU | Team |
|----|--------|-----|--------------|-----|------|
| **S1** | Customer Support Chatbot | GPT-4o (OpenAI API) | Direct API + RAG (top-5) | ~8,400 | 11 |
| **S2** | AI Code Assistant (IDE Plugin) | Llama 3.3 70B, Fine-tuned | FIM, Streaming | ~3,200 | 7 |
| **S3** | Document Summarization & QA | Gemini 1.5 Pro | Long-context (1M), RAG | ~1,900 | 5 |
| **S4** | Medical Triage Assistant | Llama 3.1 70B (self-hosted) | Agentic, Tool-use, HIPAA | ~620 | 14 |

Annotated case study documentation: `supplementary/annotated_case_studies/`  
System configurations: `configs/system_profiles/S1–S4_*.yaml`

---

## Key Empirical Results

**Study period:** October 1 – December 31, 2024 (92 days)  
**Total observations:** 3,400 (≈850 per system)  
**Metric collection completeness:** 97.3% (22/24 metrics × 4 systems)

### Table 4: Mean QALIS Scores per System and Dimension

| Dimension | S1: Chatbot | S2: Code Asst | S3: Doc QA | S4: Med Triage | Overall Mean | Std Dev |
|-----------|-------------|---------------|------------|----------------|--------------|---------|
| Functional Correctness | 7.8 | **8.9** | 8.2 | 7.1 | 8.00 | 0.77 |
| Robustness | 6.2 | 7.8 | 6.8 | **8.3** | 7.28 | 0.88 |
| Semantic Faithfulness | 8.1 | 7.3 | **9.1** | 8.6 | 8.28 | 0.72 |
| Safety & Security | 7.4 | 8.8 | 7.9 | **9.2** | 8.33 | 0.78 |
| Transparency | 5.6 | 6.2 | 7.5 | **8.9** | 7.05 | 1.35 |
| System Integration | **8.3** | 7.1 | 8.6 | 6.8 | 7.70 | 0.78 |
| **Composite** | **7.23** | **7.68** | **8.02** | **8.15** | **7.77** | **0.40** |

### QALIS vs Baselines

QALIS outperformed all three baselines across all six dimensions (Wilcoxon signed-rank, p<0.01, Bonferroni-corrected).

| Approach | FC | RO | SF | SS | TI | IQ |
|----------|----|----|----|----|----|-----|
| **QALIS** | **0.89** | **0.81** | **0.87** | **0.91** | **0.78** | **0.84** |
| ISO 25010 | 0.67 | 0.54 | 0.31 | 0.58 | 0.29 | 0.71 |
| HELM | 0.74 | 0.69 | 0.62 | 0.49 | 0.38 | 0.22 |
| MLflow | 0.51 | 0.43 | 0.28 | 0.61 | 0.19 | 0.77 |

**Key longitudinal finding:** By Month 3, QALIS-monitored systems showed 81% reduction in undetected hallucination events, 77% reduction in undetected integration errors, and 68% earlier average detection across all defect categories.

---

## Replication

All materials for full replication are included:

```bash
# Full replication
python supplementary/replication_package/replicate_all_results.py

# Check replication checklist
cat supplementary/replication_package/replication_checklist.md

# View known deviations
cat supplementary/replication_package/known_deviations.md
```

---


## License

Code and framework specification: [MIT License](LICENSE)  

---
