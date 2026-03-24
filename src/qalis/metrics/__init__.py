"""
QALIS Metrics Package
=====================

Exposes all six dimension metric classes.

Dimensions → Classes:
    FC  FunctionalCorrectnessMetrics  (FC-1 through FC-4)
    RO  RobustnessMetrics             (RO-1 through RO-5)
    SF  SemanticFaithfulnessMetrics   (SF-1 through SF-3)
    SS  SafetySecurityMetrics         (SS-1 through SS-4)
    TI  TransparencyMetrics           (TI-1 through TI-4)
    IQ  SystemIntegrationMetrics      (IQ-1 through IQ-4)

Paper reference: §4.2 (metric operationalisation), Table 3.
"""

from qalis.metrics.functional_correctness import FunctionalCorrectnessMetrics
from qalis.metrics.robustness import RobustnessMetrics
from qalis.metrics.semantic_faithfulness import SemanticFaithfulnessMetrics
from qalis.metrics.safety_security import SafetySecurityMetrics
from qalis.metrics.transparency import TransparencyMetrics
from qalis.metrics.system_integration import SystemIntegrationMetrics

__all__ = [
    "FunctionalCorrectnessMetrics",
    "RobustnessMetrics",
    "SemanticFaithfulnessMetrics",
    "SafetySecurityMetrics",
    "TransparencyMetrics",
    "SystemIntegrationMetrics",
]

# Convenience mapping: short dimension key → metric class
DIMENSION_CLASSES = {
    "FC": FunctionalCorrectnessMetrics,
    "RO": RobustnessMetrics,
    "SF": SemanticFaithfulnessMetrics,
    "SS": SafetySecurityMetrics,
    "TI": TransparencyMetrics,
    "IQ": SystemIntegrationMetrics,
}
