"""
QALIS: Quality Assessment Framework for LLM-Integrated Software Systems
=======================================================================

A multi-dimensional quality assessment framework providing 24 operationalized
metrics across 6 quality dimensions and 4 architectural layers for production
LLM-integrated software systems.

Paper: QUATIC 2025 — Special Issue on Software Quality in an AI-Driven World

Layers:
    Layer 1: Input Quality
    Layer 2: Model Behavior
    Layer 3: Output Quality
    Layer 4: System Integration Quality

Dimensions:
    FC: Functional Correctness (FC-1 through FC-4)
    RO: Robustness (RO-1 through RO-5)
    SF: Semantic Faithfulness (SF-1 through SF-3)
    SS: Safety & Security (SS-1 through SS-4)
    TI: Transparency & Interpretability (TI-1 through TI-4)
    IQ: System Integration Quality (IQ-1 through IQ-4)
"""

__version__ = "1.0.0"
__author__ = "[Withheld for double-blind review]"
__license__ = "MIT"

from qalis.framework import QALISFramework
from qalis.result import QALISResult, DimensionScore

__all__ = [
    "QALISFramework",
    "QALISResult",
    "DimensionScore",
]
