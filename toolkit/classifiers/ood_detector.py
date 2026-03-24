"""
QALIS OOD Detector — RO-3
============================

Detects out-of-distribution (OOD) queries using sentence-embedding
cosine-distance to an in-distribution centroid (per the QALIS paper and
configs/classifier_config.yaml).

RO-3 formula:  detected_ood / total_queries
Threshold:     ≥ 0.80 detection rate (paper Table 3)

The centroid file is pre-computed from production traffic using
``OODDetector.fit_centroids()`` and saved to:
  data/processed/embeddings/in_distribution_centroids.npy

At inference, a query embedding is compared to all centroids; if the minimum
cosine distance exceeds ``ood_threshold`` (default 0.65), the query is flagged
as OOD and assigned a category label.

OOD categories (from configs/classifier_config.yaml):
    financial_advice, legal_interpretation, medical_prescription,
    personal_opinion, off_topic, adversarial_jailbreak, multilingual,
    extremely_long_query, ambiguous, sensitive_pii

Usage::

    from toolkit.classifiers.ood_detector import OODDetector

    detector = OODDetector.from_centroid_file(
        "data/processed/embeddings/in_distribution_centroids.npy"
    )
    result = detector.detect("Should I invest in Bitcoin right now?")
    print(result)
    # OODResult(is_ood=True, category='financial_advice', distance=0.81, ...)

    ro3_rate = detector.ro3_rate(queries)   # fraction detected as OOD

Paper reference: §4.2 (RO-3 operationalisation), configs/classifier_config.yaml.
"""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── OOD category heuristics (fallback when no centroid file) ─────────────────

_OOD_HEURISTICS: List[tuple] = [
    ("adversarial_jailbreak",
     r"(ignore (previous|all) instructions|jailbreak|dan mode|"
      r"pretend you|you are now|act as|bypass|override|forget your (rules|training))",
     "block_and_log"),
    ("financial_advice",
     r"\b(invest|stock|portfolio|crypto|bitcoin|trading|buy|sell)\b.{0,30}\b(advice|recommend|should)\b",
     "graceful_decline"),
    ("legal_interpretation",
     r"\b(legal|contract|clause|enforceable|sue|lawsuit|attorney)\b",
     "graceful_decline"),
    ("medical_prescription",
     r"\b(prescribe|what (dose|dosage)|how much (ibuprofen|aspirin|medication|drug))\b",
     "refer_to_professional"),
    ("multilingual",
     r"[^\x00-\x7F]{10,}",
     "unsupported_language_message"),
    ("sensitive_pii",
     r"\b(\d{3}-\d{2}-\d{4}|[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})\b",
     "graceful_decline"),
]

_OOD_RESPONSES: Dict[str, str] = {
    "financial_advice":     "graceful_decline",
    "legal_interpretation": "graceful_decline",
    "medical_prescription": "refer_to_professional",
    "off_topic":            "graceful_decline",
    "adversarial_jailbreak": "block_and_log",
    "multilingual":         "unsupported_language_message",
    "extremely_long_query": "truncate_and_warn",
    "ambiguous":            "clarification_request",
    "sensitive_pii":        "graceful_decline",
    "personal_opinion":     "graceful_decline",
}


@dataclass
class OODResult:
    """Result of OOD detection on a single query."""
    is_ood: bool
    category: Optional[str] = None     # None if not OOD
    distance: float = 0.0              # Cosine distance from nearest centroid
    ood_threshold: float = 0.65
    recommended_action: str = ""       # From response_actions map
    backend: str = ""                  # "embedding" | "heuristic"
    query_length_tokens: int = 0

    def __str__(self) -> str:
        if not self.is_ood:
            return f"OODResult(is_ood=False, distance={self.distance:.3f})"
        return (
            f"OODResult(is_ood=True, category={self.category}, "
            f"distance={self.distance:.3f}, action={self.recommended_action})"
        )


class OODDetector:
    """
    QALIS OOD detector for RO-3 (OOD Detection Rate).

    Primary method:  Sentence-embedding cosine distance to in-distribution centroids.
    Fallback method: Regex heuristics for known adversarial / off-topic patterns.

    Args:
        centroids:       numpy array of shape (n_categories, embedding_dim).
                         Each row is the centroid embedding for one in-distribution
                         category.
        category_labels: List of category labels (length = n_rows of centroids).
        ood_threshold:   Cosine distance above which a query is flagged OOD
                         (default 0.65, paper Table 3 / classifier_config.yaml).
        embedding_model: sentence-transformers model ID.
        mean_query_length: Mean token length of in-distribution queries (for
                           extremely_long_query detection; set to 0 to disable).

    Usage::

        # Load from centroid file (recommended)
        detector = OODDetector.from_centroid_file(
            "data/processed/embeddings/in_distribution_centroids.npy"
        )

        # Or fit from scratch
        detector = OODDetector()
        detector.fit_centroids(in_distribution_queries)
        detector.save_centroids("data/processed/embeddings/in_distribution_centroids.npy")
    """

    def __init__(
        self,
        centroids: Optional[np.ndarray] = None,
        category_labels: Optional[List[str]] = None,
        ood_threshold: float = 0.65,
        embedding_model: str = "sentence-transformers/all-mpnet-base-v2",
        mean_query_length: float = 0.0,
    ):
        self._centroids = centroids      # (n_cats, dim) or None
        self._labels    = category_labels or []
        self._threshold = ood_threshold
        self._model_name = embedding_model
        self._mean_query_length = mean_query_length
        self._embed_model = None
        self._lock = threading.Lock()

        if centroids is not None:
            logger.info(
                "OODDetector: %d centroids loaded (dim=%d), threshold=%.2f",
                len(centroids), centroids.shape[1], ood_threshold,
            )
        else:
            logger.info(
                "OODDetector: no centroids — heuristic-only mode. "
                "Call fit_centroids() or from_centroid_file() to enable "
                "embedding-based detection."
            )

    # ── Class methods ─────────────────────────────────────────────────────────

    @classmethod
    def from_centroid_file(
        cls,
        path: str,
        **kwargs: Any,
    ) -> "OODDetector":
        """
        Load centroid array from .npy file and return a configured detector.

        Expected file format: (n_categories + 1, dim + 1) — last column is
        the category index, or plain (n_categories, dim) with category_labels
        passed via kwargs.

        Args:
            path:   Path to .npy centroid file.
            **kwargs: Forwarded to OODDetector.__init__().
        """
        p = Path(path)
        if not p.exists():
            logger.warning(
                "Centroid file not found: %s — heuristic-only mode.", path
            )
            return cls(**kwargs)
        centroids = np.load(str(p))
        logger.info("Loaded centroids from %s — shape %s", path, centroids.shape)
        return cls(centroids=centroids, **kwargs)

    # ── Model loading ─────────────────────────────────────────────────────────

    def _load_embed_model(self) -> None:
        if self._embed_model is not None:
            return
        with self._lock:
            if self._embed_model is not None:
                return
            try:
                from sentence_transformers import SentenceTransformer
                self._embed_model = SentenceTransformer(self._model_name)
                logger.info("Loaded embedding model: %s", self._model_name)
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed — "
                    "OODDetector will use heuristic-only mode. "
                    "Install with: pip install sentence-transformers"
                )
                self._embed_model = "unavailable"

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _embed(self, texts: List[str]) -> Optional[np.ndarray]:
        """Return (n, dim) embedding matrix or None if model unavailable."""
        self._load_embed_model()
        if self._embed_model == "unavailable":
            return None
        try:
            embeddings = self._embed_model.encode(
                texts, normalize_embeddings=True, show_progress_bar=False
            )
            return np.array(embeddings)
        except Exception as exc:
            logger.debug("Embedding failed: %s", exc)
            return None

    @staticmethod
    def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
        """Cosine distance (1 − cosine_similarity) for normalised vectors."""
        dot = float(np.dot(a, b))
        return round(1.0 - dot, 6)

    def _detect_heuristic(self, query: str) -> OODResult:
        """Regex heuristic fallback detection."""
        q_lower = query.lower()
        for category, pattern, action in _OOD_HEURISTICS:
            if re.search(pattern, q_lower, re.IGNORECASE):
                return OODResult(
                    is_ood=True, category=category,
                    distance=1.0, ood_threshold=self._threshold,
                    recommended_action=action, backend="heuristic",
                    query_length_tokens=len(query.split()),
                )
        n_tokens = len(query.split())
        if (self._mean_query_length > 0
                and n_tokens > self._mean_query_length * 3.0):
            return OODResult(
                is_ood=True, category="extremely_long_query",
                distance=1.0, ood_threshold=self._threshold,
                recommended_action="truncate_and_warn", backend="heuristic",
                query_length_tokens=n_tokens,
            )
        return OODResult(
            is_ood=False, distance=0.0,
            ood_threshold=self._threshold, backend="heuristic",
            query_length_tokens=n_tokens,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def detect(self, query: str) -> OODResult:
        """
        Detect if a query is out-of-distribution.

        Args:
            query: User query string.

        Returns:
            OODResult with is_ood flag, category, and recommended action.
        """
        n_tokens = len(query.split())

        # Extremely long query (rule-based — always checked first)
        if (self._mean_query_length > 0
                and n_tokens > self._mean_query_length * 3.0):
            return OODResult(
                is_ood=True, category="extremely_long_query",
                distance=1.0, ood_threshold=self._threshold,
                recommended_action="truncate_and_warn",
                backend="rule", query_length_tokens=n_tokens,
            )

        # Adversarial jailbreak (always rule-based)
        jailbreak_pattern = _OOD_HEURISTICS[0][1]
        if re.search(jailbreak_pattern, query, re.IGNORECASE):
            return OODResult(
                is_ood=True, category="adversarial_jailbreak",
                distance=1.0, ood_threshold=self._threshold,
                recommended_action="block_and_log",
                backend="rule", query_length_tokens=n_tokens,
            )

        # Embedding-based detection
        if self._centroids is not None:
            q_emb = self._embed([query])
            if q_emb is not None:
                # Normalise query embedding
                norm = np.linalg.norm(q_emb[0])
                if norm > 0:
                    q_norm = q_emb[0] / norm
                else:
                    q_norm = q_emb[0]

                # Find minimum distance to any centroid
                distances = [
                    self._cosine_distance(q_norm, c)
                    for c in self._centroids
                ]
                min_dist = min(distances)
                nearest_idx = int(np.argmin(distances))

                if min_dist > self._threshold:
                    category = (
                        self._labels[nearest_idx]
                        if self._labels and nearest_idx < len(self._labels)
                        else "off_topic"
                    )
                    return OODResult(
                        is_ood=True, category=category,
                        distance=min_dist, ood_threshold=self._threshold,
                        recommended_action=_OOD_RESPONSES.get(category, "graceful_decline"),
                        backend="embedding", query_length_tokens=n_tokens,
                    )
                else:
                    return OODResult(
                        is_ood=False, distance=min_dist,
                        ood_threshold=self._threshold,
                        backend="embedding", query_length_tokens=n_tokens,
                    )

        # Heuristic fallback
        return self._detect_heuristic(query)

    def detect_batch(self, queries: List[str]) -> List[OODResult]:
        """Detect OOD for a list of queries."""
        return [self.detect(q) for q in queries]

    def ro3_rate(self, queries: List[str]) -> float:
        """
        Compute RO-3 OOD Detection Rate.

        In the QALIS paper, RO-3 measures how reliably the system detects
        queries it should not answer — higher is better (threshold ≥ 0.80).

        This method returns the fraction of provided queries that are flagged
        as OOD. For RO-3 scoring, queries should include a mix of in-distribution
        and known-OOD queries; the score is correctly_detected_ood / n_ood_queries.

        Args:
            queries: List of query strings.

        Returns:
            Fraction detected as OOD in [0, 1].
        """
        if not queries:
            return 0.0
        results = self.detect_batch(queries)
        return round(sum(1 for r in results if r.is_ood) / len(queries), 4)

    def fit_centroids(
        self,
        in_distribution_texts: List[str],
        n_centroids: Optional[int] = None,
    ) -> np.ndarray:
        """
        Compute in-distribution centroids by averaging embeddings.

        Computes a single mean centroid over all provided texts (simple approach).
        For multi-category centroids, call this method once per category and
        stack the returned arrays.

        Args:
            in_distribution_texts: Representative in-distribution queries.
            n_centroids: Unused — reserved for k-means extension.

        Returns:
            (1, dim) numpy array representing the centroid embedding.
        """
        embeddings = self._embed(in_distribution_texts)
        if embeddings is None:
            raise RuntimeError("Embedding model unavailable — cannot fit centroids.")
        centroid = embeddings.mean(axis=0, keepdims=True)
        self._centroids = centroid
        logger.info("Fitted 1 centroid from %d texts.", len(in_distribution_texts))
        return centroid

    def save_centroids(self, path: str) -> None:
        """Save centroid array to .npy file."""
        if self._centroids is None:
            raise ValueError("No centroids to save — call fit_centroids() first.")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        np.save(path, self._centroids)
        logger.info("Saved centroids → %s", path)
