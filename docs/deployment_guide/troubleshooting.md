# Troubleshooting Guide

Common issues and solutions when deploying QALIS.

---

## NLI Classifier Issues

### "CUDA out of memory" during SF evaluation

```python
# Reduce batch size in configs/nli_classifier_config.yaml
model:
  batch_size: 16          # Reduce from 32
  fp16: true              # Ensure half-precision enabled

# Or force CPU for SF metrics only
collector = QALISCollector(system_id="MY_SYS", device="cpu")
```

### NLI scores seem too low / too many false positives

This typically occurs for domain-specific language. Characterise false positives
during the 2-week onboarding period:

```python
fp_analysis = collector.characterise_false_positives(
    sample_logs="path/to/logs.jsonl",
    n_samples=200
)
print(fp_analysis.common_patterns)
# Update configs/nli_classifier_config.yaml: false_positive_characterisation section
```

### Cold start latency (first request takes 30+ seconds)

Pre-load models at startup:
```python
collector = QALISCollector(system_id="MY_SYS", lazy_load=False)
# Models load at construction, not first evaluate() call
```

---

## PII Detection Issues

### High false positive rate on domain-specific terms

Add domain allowlist entries to `configs/classifier_config.yaml`:
```yaml
pii_detection:
  domain_allowlists:
    my_domain:
      - "Order #"           # Not PII — order reference numbers
      - "Account type"      # Not PII — product category
```

### spaCy model not found

```bash
python -m spacy download en_core_web_trf
# If network restricted:
# Download model manually from https://spacy.io/models/en
# and install: pip install /path/to/en_core_web_trf-3.x.x.tar.gz
```

---

## Metric Collection Issues

### IQ-4 Observability Index below 0.90

```python
report = collector.validate_instrumentation()
for gap in report.gaps:
    print(f"Missing: {gap.metric_id} — {gap.reason} — {gap.remediation}")
```

Common gaps and remediations:
- **IQ-2 missing**: Add OpenTelemetry tracing to your LLM API calls
- **TI-4 low**: Ensure all 13 required audit fields are logged per interaction
- **SF-2 missing**: Add source citation extraction to RAG pipeline responses
- **SS-1 missing**: Verify Perspective API key is set (`PERSPECTIVE_API_KEY`)

### Realtime metrics gaps / missing 5-minute windows

Check that the background flush worker is running:
```python
stream = QALISStreamCollector(system_id="MY_SYS")
print(f"Flush worker alive: {stream.flush_worker.is_alive()}")
print(f"Queue size: {stream.queue.qsize()}")
```

---

## CI/CD Integration Issues

### Quality gate always passes despite regressions

Ensure `compare_to="last_stable_release"` is set and that a baseline snapshot
exists:
```python
collector.save_quality_snapshot(tag="stable-v1.2.0")
# Then in CI:
gate = collector.run_quality_gate(compare_to="stable-v1.2.0")
```

### GitHub Actions workflow timeout

The NLI inference step is the bottleneck. Reduce CI eval set size:
```yaml
# configs/ci_cd_config.yaml
eval_sets:
  sf3_regression_suite:
    size: 100           # Reduce from 300 for faster CI
```

---

## Performance Tuning

### Reducing evaluation latency for real-time use

1. **Sample SF metrics**: Run NLI on 20% of traffic; use RO-4 as proxy for the rest
2. **Cache embeddings**: Enable Redis cache in `embedding_config.yaml`
3. **Async evaluation**: Use `QALISStreamCollector` — evaluation runs in background
4. **Skip expensive metrics in hot path**: Collect TI-2, FC-4 on scheduled basis only

### Memory usage too high

```python
# Release model memory between evaluation runs
collector.release_models()          # Frees GPU/CPU memory for NLI/embedding models
# Models will be re-loaded lazily on next evaluate() call
```

---

## Data and Results Issues

### Metric values differ slightly from paper

Expected — the study data was generated with fixed random seeds (42 and 123) but
slight numerical differences may occur due to library version differences. Check:

```python
import numpy, scipy, transformers
print(numpy.__version__)        # Expected: 1.26.x
print(scipy.__version__)        # Expected: 1.11.x
print(transformers.__version__) # Expected: 4.40.x
```

### Correlation matrix values differ from Figure 4

Ensure you are loading from the processed correlation file, not recomputing from raw:
```python
import json
corr = json.load(open("data/processed/correlations/metric_correlation_matrix.json"))
print(f"SF-3 vs RO-4: {corr['paper_highlighted']['SF3_vs_RO4']}")  # Should be 0.61
```

### Figures not generated (matplotlib missing)

```bash
pip install matplotlib seaborn
python analysis/generate_all_figures.py
```
