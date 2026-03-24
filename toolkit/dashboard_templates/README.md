# QALIS Dashboard Templates

Two monitoring templates are provided for visualizing QALIS quality metrics in production.

## Files

| File | Description |
|------|-------------|
| `grafana_qalis_overview.json` | Grafana dashboard — import directly via Grafana UI |
| `qalis_html_report_template.html` | Self-contained HTML report template (Handlebars-style tokens) |

---

## Grafana Dashboard (`grafana_qalis_overview.json`)

### Prerequisites
- Grafana ≥ 10.0 with a Prometheus datasource configured
- QALIS dashboard API running and Prometheus scrape endpoint enabled:
  ```bash
  uvicorn src.qalis.dashboard.app:app --port 8080
  # Metrics available at http://localhost:8080/metrics
  ```
- Prometheus scraping `http://localhost:8080/metrics` (add to `prometheus.yml`)

### Import
1. Open Grafana → **Dashboards → Import**
2. Upload `grafana_qalis_overview.json` or paste its contents
3. Select your Prometheus datasource
4. Select a `system_id` from the dropdown

### Panels included
- **Composite Score** gauge with colour-coded thresholds (red < 6.0, yellow < 7.0, green ≥ 8.0)
- **Six dimension scores** as stat panels (FC, RO, SF, SS, TI, IQ)
- **30-day composite trend** time series
- **Real-time panels**: SS-1 toxicity, IQ-2 latency P95, IQ-1 API availability
- **SF-3 hallucination rate** daily trend with threshold line
- **Active violations** table

### Prometheus metrics exposed by QALIS dashboard

| Metric name | Labels | Description |
|-------------|--------|-------------|
| `qalis_composite_score` | `system_id` | Composite 0–10 quality score |
| `qalis_dimension_score` | `system_id`, `dimension` | Per-dimension score (FC/RO/SF/SS/TI/IQ) |
| `qalis_metric_value` | `system_id`, `metric_id` | Raw metric value (e.g. SS-1 toxicity rate) |
| `qalis_threshold_violation` | `system_id`, `metric_id`, `dimension`, `severity` | 1 when threshold violated |
| `qalis_observations_total` | `system_id` | Total observations ingested |

---

## HTML Report Template (`qalis_html_report_template.html`)

A standalone single-file HTML report rendered from QALIS quality gate results.
Uses Handlebars-style `{{token}}` placeholders — replace with your values or render
via the `toolkit/exporters/` module.

### Token reference

| Token | Type | Example |
|-------|------|---------|
| `{{system_name}}` | string | `"Customer Support Chatbot"` |
| `{{report_date}}` | string | `"2024-12-31"` |
| `{{composite_score}}` | string | `"7.77"` |
| `{{composite_class}}` | `pass`/`warn`/`fail` | `"pass"` |
| `{{gate_status}}` | string | `"PASS"` / `"FAIL"` |
| `{{gate_violations}}` | int | `0` |
| `{{gate_regressions}}` | int | `1` |
| `{{dimensions}}` | array | `[{abbrev, name, score, color}, ...]` |
| `{{metrics}}` | array | `[{id, name, value_formatted, threshold_formatted, bar_pct, color}, ...]` |
| `{{violations}}` | array | `[{metric_id, dimension, value_formatted, severity, recommended_action}, ...]` |
| `{{regressions}}` | array | `[{metric_id, current_formatted, baseline_formatted, delta_formatted}, ...]` |

### Generating a report programmatically

```python
from toolkit.exporters.prometheus_exporter import PrometheusExporter
from toolkit.ci_gate.quality_gate import QALISQualityGate
import re

gate = QALISQualityGate("MY_SYS", "configs/ci_cd_config.yaml")
result = gate.run()

with open("toolkit/dashboard_templates/qalis_html_report_template.html") as f:
    template = f.read()

# Replace scalar tokens
replacements = {
    "system_name":       "My System",
    "report_date":       "2024-12-31",
    "composite_score":   f"{result.composite_score:.2f}",
    "composite_class":   "pass" if result.composite_score >= 7.0 else "fail",
    "gate_status":       "PASS" if result.passed else "FAIL",
    "gate_class":        "pass" if result.passed else "fail",
    "gate_violations":   str(len(result.failures)),
    "gate_regressions":  str(len(result.regressions)),
    # ... add dimension/metric/violation arrays as needed
}
for token, value in replacements.items():
    template = template.replace(f"{{{{{token}}}}}", value)

with open("reports/qalis_report.html", "w") as f:
    f.write(template)
```

See `src/qalis/dashboard/app.py` for the live FastAPI dashboard API.

---

*Paper reference: §3.3 (monitoring instrumentation), §4.4 (IQ-4 Observability), §4.5 (Toolkit)*
