# QALIS Toolkit

Production-ready Python toolkit for instrumenting LLM-integrated software systems
with QALIS quality metrics.

## Structure

```
toolkit/
├── README.md
├── __init__.py
│
├── collectors/                        ← Core metric collection
│   ├── __init__.py
│   └── qalis_collector.py            ← QALISCollector + QALISStreamCollector
│
├── ci_gate/                           ← CI/CD quality gate evaluation engine
│   ├── __init__.py
│   └── quality_gate.py               ← QALISQualityGate (blocks deployments)
│
├── ci_cd_integration/                 ← Pipeline integration helpers
│   ├── __init__.py
│   ├── github_actions.py             ← GitHub Actions runner + step summary
│   └── deployment_hooks.py          ← Pre/post-deploy lifecycle hooks
│
├── classifiers/                       ← ML classifiers for SS / RO metrics
│   ├── __init__.py
│   ├── toxicity_classifier.py        ← SS-1  Perspective API + toxic-bert
│   ├── pii_detector.py               ← SS-2  spaCy NER + regex patterns
│   ├── ood_detector.py               ← RO-3  Embedding cosine-distance OOD
│   └── policy_classifier.py          ← SS-4  Rule engine + BART-MNLI fallback
│
├── exporters/                         ← Metric export adapters
│   ├── __init__.py
│   ├── prometheus_exporter.py         ← Prometheus /metrics endpoint
│   └── mlflow_exporter.py             ← MLflow experiment logging
│
└── integrations/                      ← LLM framework integrations
    ├── __init__.py
    └── langchain_callback.py          ← LangChain callback handler
```

## Quick Start

```python
from toolkit.collectors.qalis_collector import QALISCollector

collector = QALISCollector(
    system_id="my-chatbot",
    domain="customer_support",
    llm_provider="openai",
    risk_level="medium"
)

result = collector.evaluate(
    query="What is your return policy?",
    response="We accept returns within 30 days of purchase.",
    context="Returns are accepted within 30 days. Items must be unused.",
    metadata={"latency_ms": 412}
)

print(result.summary_report())
# QALIS Score: 7.85/10  [FC:8.2✓ RO:7.5✓ SF:8.1✓ SS:8.0✓ TI:6.2⚠ IQ:8.9✓]
```

## Streaming Integration

```python
from toolkit.collectors.qalis_collector import QALISStreamCollector

stream = QALISStreamCollector(system_id="MY_SYS", flush_interval_seconds=300)

@app.after_request
def collect_qalis(response):
    stream.record(
        query=request.json["query"],
        response=response.json["answer"],
        context=request.json.get("context"),
        latency_ms=float(response.headers.get("X-Latency-Ms", 0))
    )
    return response
```

## CI/CD Quality Gate

```python
from toolkit.ci_gate.quality_gate import QALISQualityGate

gate = QALISQualityGate(
    system_id="MY_SYS",
    config_path="configs/ci_cd_config.yaml"
)
result = gate.run(compare_to="last_stable_release")
if not result.passed:
    exit(1)
```

## Paper Reference

Paper: QUATIC 2025 — *QALIS: A Multi-Dimensional Quality Assessment Framework
for Large Language Model-Integrated Software Systems.*  
Paper section: §4.5 (Toolkit Design).

## Classifiers

SS and RO metric collection backed by dedicated ML classifiers:

```python
from toolkit.classifiers.toxicity_classifier import ToxicityClassifier
from toolkit.classifiers.pii_detector import PIIDetector
from toolkit.classifiers.ood_detector import OODDetector
from toolkit.classifiers.policy_classifier import PolicyClassifier

# SS-1: Toxicity Rate
clf = ToxicityClassifier(api_key="...", domain="customer_support")
ss1 = clf.ss1_rate(response_texts)   # ≤ 0.005 to pass

# SS-2: PII Leakage Rate
pii = PIIDetector(domain="healthcare")
ss2 = pii.ss2_rate(response_texts)   # ≤ 0.0001 (healthcare) to pass

# RO-3: OOD Detection Rate
ood = OODDetector.from_centroid_file("data/processed/embeddings/in_distribution_centroids.npy")
result = ood.detect("Should I invest in Bitcoin?")
# OODResult(is_ood=True, category='financial_advice', action='graceful_decline')

# SS-4: Policy Compliance Rate
pc = PolicyClassifier(domain="healthcare")
ss4 = pc.ss4_rate(response_texts)   # ≥ 0.98 to pass
```

## CI/CD Integration

Full pipeline lifecycle hooks and GitHub Actions runner:

```python
# Deployment script
from toolkit.ci_cd_integration.deployment_hooks import DeploymentHooks, QALISGateFailure

hooks = DeploymentHooks(
    system_id="MY_SYS",
    trigger="model_version_update",
    version="v2.1.0",
)
try:
    hooks.pre_deploy()           # Raises QALISGateFailure if blocked
    # ... deploy here ...
    hooks.post_deploy()          # Save new stable baseline
except QALISGateFailure as e:
    print(e)
    sys.exit(1)
```

```bash
# GitHub Actions step
python -m toolkit.ci_cd_integration.github_actions \
    --system-id MY_SYS \
    --config-path configs/ci_cd_config.yaml \
    --compare-to last_stable_release
```
