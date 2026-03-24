# QALIS Framework Specification v1.0

## Overview

QALIS organizes quality concerns into a **four-layer hierarchy** mirroring
the architectural structure of a typical LLM-integrated system.

### Layer 1: Input Quality Layer
Governs quality of signals entering the LLM component:
- **Prompt Engineering Quality** — instruction clarity, few-shot example selection, format specification
- **Context Completeness** — adequacy of retrieved/provided context relative to query information requirements
- **Data Integrity** — upstream pipeline corruption, truncation, encoding errors
- **Bias Assessment** — demographic/representational biases in prompt templates or retrieval mechanisms

### Layer 2: Model Behavior Layer
Characterizes intrinsic LLM quality in isolation:
- **Functional Correctness** (FC) → Metrics: FC-1, FC-2, FC-3, FC-4
- **Robustness** (RO) → Metrics: RO-1, RO-2, RO-3, RO-4, RO-5

### Layer 3: Output Quality Layer
Evaluates LLM response properties as experienced by users:
- **Semantic Faithfulness** (SF) → Metrics: SF-1, SF-2, SF-3
- **Safety & Security** (SS) → Metrics: SS-1, SS-2, SS-3, SS-4
- **Transparency & Interpretability** (TI) → Metrics: TI-1, TI-2, TI-3, TI-4

### Layer 4: System Integration Quality Layer
Quality at the LLM-host system boundary:
- **System Integration Quality** (IQ) → Metrics: IQ-1, IQ-2, IQ-3, IQ-4

## Cross-Layer Interactions

Key causal dependencies documented:
- **Poor context completeness (L1) → Hallucination (L3-SF)**: When retrieved chunks lack
  relevant information, the model draws on training data, generating unsupported claims.
- **Latency degradation (L4-IQ-2) precedes availability failure (L4-IQ-1)**: r=0.74 in empirical study.
- **Low consistency (L2-RO-4) predicts hallucination (L3-SF-3)**: r=0.61 in empirical study.
  Cheaper consistency metrics can serve as early warning for expensive faithfulness evaluation.

## Framework Instantiation

Four-step process for tailoring QALIS to a specific system:
1. Identify applicable layers based on system architecture
2. Select relevant metrics from each layer based on domain and risk level
3. Configure thresholds using provided defaults or domain-specific calibration
4. Establish monitoring cadences and alert routing

See `supplementary/replication_package/instantiation_guide.md` for detailed guidance.
