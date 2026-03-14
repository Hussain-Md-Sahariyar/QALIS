# QALIS API Reference

Complete reference for the QALIS Python toolkit.

---

## QALISCollector

The main entry point for production metric collection.

```python
from toolkit.collectors.qalis_collector import QALISCollector
```

### Constructor

```python
QALISCollector(
    system_id: str,
    config_path: str = "configs/qalis_config.yaml",
    thresholds_path: str = "configs/metrics_thresholds.yaml",
    nli_model: str = "cross-encoder/nli-deberta-v3-large",
    device: str = "auto",          
    lazy_load: bool = True, # Load NLI/classifier models on first use
    audit_logging: bool = True
)
```

**Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_id` | str | required | System identifier (S1–S4 in study, or custom) |
| `config_path` | str | `configs/qalis_config.yaml` | Path to master config |
| `thresholds_path` | str | `configs/metrics_thresholds.yaml` | Metric thresholds |
| `nli_model` | str | DeBERTa-NLI | HuggingFace model ID for SF metrics |
| `device` | str | `"auto"` | Inference device |
| `lazy_load` | bool | `True` | Defer model loading until first use |
| `audit_logging` | bool | `True` | Log all evaluations for TI-4 |

---

### evaluate()

Evaluate a single query-response pair across all applicable QALIS metrics.

```python
result: QALISResult = collector.evaluate(
    query: str,
    response: str,
    context: str | None = None, # Grounding context (RAG systems)
    metadata: dict | None = None, # latency_ms, session_id, user_hash, etc.
    dimensions: list[str] | None = None,  # Subset: ["FC","SF","SS"] etc.
)
```

**Returns: `QALISResult`**

```python
@dataclass
class QALISResult:
    system_id: str
    timestamp: datetime
    composite_score: float             
    dimension_scores: dict[str, float]  
    metrics: dict[str, float]          
    threshold_violations: list[Violation]
    alerts: list[Alert]
    audit_record_id: str
    collection_duration_ms: float
```

**Example**

```python
result = collector.evaluate(
    query="How do I reset my password?",
    response="Click 'Forgot Password' on the login page to receive a reset email.",
    context="Password reset: users can request a reset email from the login page.",
    metadata={"latency_ms": 412, "session_id": "sess-8841"}
)

# Check violations
for v in result.threshold_violations:
    print(f"[{v.severity}] {v.metric_id}: {v.value:.4f}")

# Access individual metrics
print(f"Hallucination rate: {result.metrics.get('SF-3', 'N/A')}")
print(f"Faithfulness: {result.metrics.get('SF-1', 'N/A')}")
```

---

### evaluate_batch()

Evaluate a list of interactions efficiently using batched inference.

```python
batch_result: QALISBatchResult = collector.evaluate_batch(
    queries: list[str],
    responses: list[str],
    contexts: list[str | None] | None = None,
    metadata: list[dict] | None = None,
    n_workers: int = 4,
    show_progress: bool = True
)
```

**Returns: `QALISBatchResult`**

```python
@dataclass
class QALISBatchResult:
    results: list[QALISResult]
    n_evaluated: int
    n_violations: int
    violation_rate: float

    def summary(self) -> BatchSummary:
        """Returns dimension means, violation counts, threshold pass rates."""

    def to_dataframe(self) -> pd.DataFrame:
        """Returns results as a pandas DataFrame."""

    def save(self, path: str) -> None:
        """Saves results to CSV or JSONL depending on file extension."""
```

---

### validate_instrumentation()

Compute IQ-4 Observability Index — verify that all applicable metrics can be
collected before going live.

```python
report: InstrumentationReport = collector.validate_instrumentation()

print(f"IQ-4 score: {report.iq4_score:.2f}")   # Target ≥ 0.90
print(f"Covered metrics: {report.n_covered}/{report.n_applicable}")
for gap in report.gaps:
    print(f"  Missing: {gap.metric_id} — {gap.reason}")
```

---

### calibrate()

Run threshold calibration on a sample of recent production logs.

```python
calibration: CalibrationResult = collector.calibrate(
    sample_logs: str | pd.DataFrame,   # Path to JSONL or DataFrame
    n_samples: int = 500,
    percentile_target: float = 0.10    # Set threshold at 10th percentile
)

print(calibration.suggested_thresholds)

# Apply calibrated thresholds
collector.apply_thresholds(calibration.suggested_thresholds)
```

---

## QALISResult — Full Schema

```python
@dataclass
class QALISResult:
    # Identity
    system_id: str
    timestamp: datetime
    query_hash: str # SHA-256 of input query
    response_hash: str # SHA-256 of response

    # Scores
    composite_score: float
    dimension_scores: dict[str, float]  
    metrics: dict[str, float] # All 24 metric values

    # Violations and alerts
    threshold_violations: list[Violation]
    alerts: list[Alert]

    # Collection metadata
    audit_record_id: str
    collection_duration_ms: float
    nli_claims_evaluated: int # Number of claims sent to NLI model
    model_versions: dict[str, str] # Classifier model versions used

    # Raw intermediate values
    nli_label_counts: dict # {"entailed": 8, "neutral": 2, "contradicted": 1}
    embedding_similarity: float | None  # Query-response cosine similarity


@dataclass
class Violation:
    metric_id: str                     
    dimension: str                     
    value: float                       
    threshold: float                   
    operator: str                      
    severity: str                      
    recommended_action: str
    causal_trace: list[str]             


@dataclass
class Alert:
    metric_id: str
    alert_type: str                  
    severity: str
    message: str
    pagerduty_triggered: bool
```

---

## Metric IDs Reference

| Metric ID | Name | Dimension | Threshold | Op |
|-----------|------|-----------|-----------|-----|
| FC-1 | Task Accuracy | FC | 0.85 | ≥ |
| FC-2 | BERTScore F1 | FC | 0.78 | ≥ |
| FC-3 | Pass@k (k=5) | FC | 0.90 | ≥ |
| FC-4 | Factual Precision | FC | 0.80 | ≥ |
| RO-1 | Perturbation Sensitivity | RO | 0.10 | ≤ |
| RO-2 | Injection Resistance Rate | RO | 0.97 | ≥ |
| RO-3 | OOD Detection Rate | RO | 0.80 | ≥ |
| RO-4 | Semantic Invariance Score | RO | 0.85 | ≥ |
| RO-5 | Adversarial Robustness Index | RO | 0.82 | ≥ |
| SF-1 | Faithfulness Score | SF | 0.88 | ≥ |
| SF-2 | Attribution Coverage | SF | 0.75 | ≥ |
| SF-3 | Hallucination Rate /1K tokens | SF | 2.0 | ≤ |
| SS-1 | Toxicity Rate | SS | 0.005 | ≤ |
| SS-2 | PII Leakage Rate | SS | 0.001 | ≤ |
| SS-3 | Injection Attack Success Rate | SS | 0.02 | ≤ |
| SS-4 | Policy Compliance Score | SS | 0.98 | ≥ |
| TI-1 | Explanation Coverage Rate | TI | 0.70 | ≥ |
| TI-2 | Explanation Faithfulness Score | TI | 0.80 | ≥ |
| TI-3 | User Interpretability Rating | TI | 3.8 | ≥ |
| TI-4 | Audit Trail Completeness | TI | 0.99 | ≥ |
| IQ-1 | API Availability Rate | IQ | 0.999 | ≥ |
| IQ-2 | P95 Response Latency (ms) | IQ | 2500 | ≤ |
| IQ-3 | Cost per Quality Unit | IQ | org-specific | — |
| IQ-4 | Observability Index | IQ | 0.90 | ≥ |
