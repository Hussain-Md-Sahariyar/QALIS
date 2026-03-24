# QALIS Documentation

**A Multi-Dimensional Quality Assessment Framework for Large Language Model-Integrated Software Systems**
*QUATIC 2025*

---

## Contents

| Document | Description |
|----------|-------------|
| [User Guide](user_guide/README.md) | Getting started, framework concepts, walkthrough |
| [API Reference](api_reference/README.md) | Full collector API, metrics catalogue, schemas |
| [Deployment Guide](deployment_guide/README.md) | Production setup, CI/CD integration, scaling |
| [Figure Descriptions](figures/figure_descriptions.md) | Paper figures 1–6 with captions and data sources |

## Quick Start

```python
from toolkit.collectors.qalis_collector import QALISCollector

collector = QALISCollector(system_id="S1", config_path="configs/qalis_config.yaml")
result = collector.evaluate(
    query="What is your return policy?",
    response="Our return policy allows returns within 30 days of purchase.",
    context="Returns are accepted within 30 days. Items must be unused."
)
print(f"Composite score: {result.composite_score:.2f}")
print(f"Violations: {result.threshold_violations}")
```

## Paper Reference

> [Author names anonymised for review]. "QALIS: A Multi-Dimensional Quality Assessment
> Framework for Large Language Model-Integrated Software Systems."
> *Proceedings of QUATIC 2025 — 18th International Conference on the Quality of
> Information and Communications Technology.* 2025.

## Framework at a Glance

QALIS assesses LLM-integrated software across **6 quality dimensions** and **24 metrics**
organised into **4 architectural layers**:

| Layer | Focus | Dimensions |
|-------|-------|------------|
| 1 — Input Quality | Prompt and context preparation | (upstream of FC/SF) |
| 2 — Model Behaviour | Functional output and robustness | FC, RO |
| 3 — Output Quality | Semantic grounding, safety, transparency | SF, SS, TI |
| 4 — System Integration | Infrastructure reliability and cost | IQ |

## Study Results Summary

| System | FC | RO | SF | SS | TI | IQ | Composite |
|--------|----|----|----|----|----|----|-----------|
| S1 — Customer Support | 7.8 | 6.2 | 8.1 | 7.4 | 5.6 | 8.3 | **7.23** |
| S2 — Code Assistant | 8.9 | 7.8 | 7.3 | 8.8 | 6.2 | 7.1 | **7.68** |
| S3 — Document QA | 8.2 | 6.8 | 9.1 | 7.9 | 7.5 | 8.6 | **8.02** |
| S4 — Medical Triage | 7.1 | 8.3 | 8.6 | 9.2 | 8.9 | 6.8 | **8.15** |
| **Mean** | 8.0 | 7.3 | 8.3 | 8.3 | 7.1 | 7.7 | **7.77** |

*Transparency (TI) was the lowest-scoring dimension (mean 7.05, σ=1.35) and the most
actionable gap identified across all four systems.*
