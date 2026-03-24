"""
QALIS Toolkit — Classifiers
=============================

ML classifiers and rule-based detectors powering the Safety & Security (SS)
and Robustness (RO) metric dimensions.

Configuration: configs/classifier_config.yaml

Classifiers:
    ToxicityClassifier    SS-1  Perspective API + toxic-bert fallback
    PIIDetector           SS-2  spaCy NER + regex patterns (GDPR/HIPAA)
    OODDetector           RO-3  Sentence-embedding cosine-distance detector
    PolicyClassifier      SS-4  Rule engine + BART-large-MNLI fallback

All classifiers are designed to be lazy-loaded (models fetched on first call)
and are thread-safe for use in streaming collectors.

Paper reference: §4.2 (SS / RO metric operationalisation), §4.5 (Toolkit).
Configuration:   configs/classifier_config.yaml
"""

from toolkit.classifiers.toxicity_classifier import ToxicityClassifier
from toolkit.classifiers.pii_detector import PIIDetector
from toolkit.classifiers.ood_detector import OODDetector
from toolkit.classifiers.policy_classifier import PolicyClassifier

__all__ = [
    "ToxicityClassifier",
    "PIIDetector",
    "OODDetector",
    "PolicyClassifier",
]
