# QALIS Deployment Guide

This guide covers deploying QALIS in a production environment, including
hardware requirements, CI/CD integration, scaling considerations, and
domain-specific configurations.

---

## 1. Infrastructure Requirements

### Minimum (Development / Small Scale)

| Component | Specification |
|-----------|--------------|
| CPU | 4 cores, 8 GB RAM |
| Storage | 20 GB (framework + small data) |
| GPU | Not required (CPU inference available) |
| Python | 3.10+ |

**Throughput**: ~5 evaluations/second (CPU NLI inference)

### Recommended (Production)

| Component | Specification |
|-----------|--------------|
| CPU | 16 cores, 32 GB RAM |
| GPU | NVIDIA A10G or better (24 GB VRAM) |
| Storage | 500 GB SSD (for embedding cache + logs) |
| Network | Low-latency access to LLM provider API |

**Throughput**: ~80 evaluations/second (GPU NLI inference, batch size 32)

### High-Volume Production (>10K req/hour)

- Deploy NLI classifier as a separate microservice (e.g. NVIDIA Triton)
- Use Redis for embedding cache (`cache_backend: redis` in `embedding_config.yaml`)
- Shard log storage by system and date
- Use async evaluation (`QALISStreamCollector` with background workers)

---

## 2. Environment Setup

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy NER model
python -m spacy download en_core_web_trf

# 4. Pre-download NLI model (recommended — avoids cold start)
python -c "
from transformers import AutoTokenizer, AutoModelForSequenceClassification
model_id = 'cross-encoder/nli-deberta-v3-large'
AutoTokenizer.from_pretrained(model_id)
AutoModelForSequenceClassification.from_pretrained(model_id)
print('NLI model downloaded.')
"

# 5. Pre-download sentence transformer
python -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
print('Embedding model downloaded.')
"

# 6. Set environment variables
export QALIS_SYSTEM_ID=MY_SYS
export PERSPECTIVE_API_KEY=your_key_here     # For SS-1 toxicity
export OPENAI_API_KEY=your_key_here          # If using OpenAI LLM
```

---

## 3. Configuration for Production

### Recommended Config Overrides

```yaml
# configs/qalis_config.yaml — production additions
logging:
  level: WARNING          # Reduce log volume in production
  file: /var/log/qalis/qalis.log

paths:
  logs: /var/log/qalis/
```

```yaml
# configs/nli_classifier_config.yaml — production tuning
model:
  device: "cuda"
  fp16: true
  batch_size: 64          # Increase for GPU throughput

performance:
  cache_embeddings: true
  cache_backend: "redis"
  cache_ttl_hours: 168
```

### Domain-Specific Threshold Tuning

Always override thresholds for high-risk domains before going live:

```yaml
# configs/system_profiles/my_clinical_system.yaml
metric_overrides:
  FC-4:
    threshold: 0.90       # Higher factual precision for medical
  SF-3:
    threshold: 1.0        # Stricter hallucination limit
  SS-2:
    threshold: 0.0001     # Near-zero PII tolerance (HIPAA)
  TI-1:
    threshold: 0.95       # All responses must have explanation (regulatory)
  TI-4:
    threshold: 0.999      # Near-complete audit trail (HIPAA)
```

---

## 4. CI/CD Integration

### GitHub Actions

The `.github/workflows/qalis_ci.yml` pipeline runs QALIS quality gates on every
model update, prompt template change, or RAG corpus update.

```yaml
# Trigger quality gate manually
gh workflow run qalis_ci.yml \
  -f system_id=MY_SYS \
  -f trigger_reason=model_version_update
```

### Blocking Deployments on Quality Regression

```python
# deploy.py — add this before deploying a new model version
from toolkit.collectors.qalis_collector import QALISCollector

collector = QALISCollector(system_id="MY_SYS")

gate_result = collector.run_quality_gate(
    eval_sets={
        "FC-1": "data/processed/eval_sets/fc1_regression_suite.csv",
        "SF-3": "data/processed/eval_sets/sf3_regression_suite.jsonl",
        "SS-1": "data/processed/eval_sets/ss1_regression_suite.csv",
    },
    compare_to="last_stable_release"
)

if not gate_result.passed:
    print("DEPLOYMENT BLOCKED — Quality gate failures:")
    for failure in gate_result.failures:
        print(f"  {failure.metric_id}: {failure.value:.4f} {failure.operator} {failure.threshold}")
    exit(1)

print("Quality gate passed. Proceeding with deployment.")
```

---

## 5. Monitoring Integration

### Prometheus / Grafana

```python
from toolkit.collectors.qalis_collector import QALISStreamCollector
from prometheus_client import Gauge, start_http_server

# Expose QALIS metrics as Prometheus gauges
qalis_fc1 = Gauge("qalis_fc1_task_accuracy", "FC-1 Task Accuracy", ["system_id"])
qalis_sf3 = Gauge("qalis_sf3_hallucination_rate", "SF-3 Hallucination Rate", ["system_id"])
qalis_iq1 = Gauge("qalis_iq1_availability", "IQ-1 API Availability", ["system_id"])
qalis_composite = Gauge("qalis_composite_score", "QALIS Composite Score", ["system_id"])

start_http_server(9090)

stream = QALISStreamCollector(system_id="MY_SYS", flush_interval_seconds=300)

@stream.on_flush
def update_prometheus(batch_result):
    means = batch_result.summary().dimension_metric_means
    qalis_fc1.labels(system_id="MY_SYS").set(means.get("FC-1", 0))
    qalis_sf3.labels(system_id="MY_SYS").set(means.get("SF-3", 0))
    qalis_composite.labels(system_id="MY_SYS").set(batch_result.summary().composite_mean)
```

### Alert Routing

Configure alert channels in `configs/monitoring_config.yaml`:

```yaml
alert_rules:
  critical:
    channels: [pagerduty, slack_critical, email_oncall]
  high:
    channels: [slack_alerts, email_team]
  medium:
    channels: [slack_monitoring]
```

---

## 6. Scaling Considerations

### NLI Inference Bottleneck

SF-1 and SF-3 (NLI-based) are the most compute-intensive metrics. Strategies:

1. **Sample-based evaluation**: Evaluate 20% of traffic for SF metrics; use
   RO-4 (semantic invariance, cheap embedding-based) as a leading indicator.
   RO-4 has r=0.61 with SF-3 — spikes in RO-4 degradation predict SF-3 problems.

2. **Separate NLI service**: Deploy DeBERTa-NLI behind a REST endpoint and
   call it asynchronously from the main evaluation pipeline.

3. **Tiered evaluation**: Run full QALIS daily on a representative 5% sample;
   run only IQ/SS realtime metrics on 100% of traffic.

### Embedding Cache

Pre-warm the OOD detection centroid cache on startup:

```python
collector = QALISCollector(system_id="MY_SYS")
collector.warm_cache()  # Loads centroids, PCA model, tokenizers
```

---

## 7. Domain-Specific Deployment Notes

### Clinical / Medical (S4 pattern)

- Set `risk_level: high` in system profile
- Apply `EU_AI_Act_high_risk` and `HIPAA` regulatory context
- Enable human-in-loop routing for confidence < 0.75
- IQ-3 (cost/quality) inapplicable if self-hosted — exclude from IQ-4 denominator
- Minimum team: 1 dedicated quality engineer + clinical SME for FC-4/TI-2 annotation

### RAG Systems (S1/S3 pattern)

- Enable SF-2 (attribution coverage) — requires citation extraction in response
- Monitor context retrieval quality separately from LLM quality
- SF-3 hallucination rate correlates with retrieval relevance — instrument retriever

### Streaming / Code Generation (S2 pattern)

- Replace FC-1 with FC-3 (Pass@k) as primary correctness metric
- Tighten IQ-2 threshold (≤1500ms for IDE responsiveness)
- TI-3 not applicable if no user-facing explanation surface
- Set `fim_mode: true` in system profile

---

## 8. Onboarding Checklist

Before treating QALIS scores as production-grade:

- [ ] IQ-4 Observability Index ≥ 0.90 (`collector.validate_instrumentation()`)
- [ ] 2-week onboarding period completed (false positive characterisation)
- [ ] Thresholds calibrated on representative traffic (`collector.calibrate()`)
- [ ] NLI classifier false positive rates documented per system
- [ ] Alert routing tested (trigger a synthetic SS-1 violation)
- [ ] CI/CD quality gate pipeline passing on current stable release
- [ ] Audit trail completeness (TI-4) verified ≥ 0.99
- [ ] Human annotation panel established for FC-4 and TI-2 (if applicable)
- [ ] Data retention policy configured in `monitoring_config.yaml`
