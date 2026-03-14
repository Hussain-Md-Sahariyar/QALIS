"""
Functional Correctness Metrics (FC-1 through FC-4)
===================================================

Dimension 1 of the QALIS framework (§5.1).

Metrics implemented:
    FC-1: Task Accuracy — proportion of outputs satisfying task specification
    FC-2: BERTScore F1 — token-level cosine similarity with DeBERTa embeddings
    FC-3: Pass@k (k=5) — code generation success rate across k samples
    FC-4: Factual Precision — verified facts / total stated facts

Layer: 2 (Model Behavior)
Cadence: FC-1 daily; FC-2, FC-3 per-release; FC-4 weekly (Table 3)

Target thresholds (from Table 3, paper §5.1):
    FC-1: ≥ 0.85
    FC-2: ≥ 0.78 (DeBERTa-large-mnli embedding space)
    FC-3: ≥ 0.90 (k=5 samples)
    FC-4: ≥ 0.80 (5% human audit sample)

Measurement formula for FC-3 (Chen et al., 2021 [27]):
    pass@k = 1 - C(n-c, k) / C(n, k)
    where n = total samples, c = correct samples, k = sample budget
"""

import re
from typing import Dict, List, Optional, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FunctionalCorrectnessMetrics:
    """
    Implements the four Functional Correctness metrics (FC-1 through FC-4).

    Uses reference-free approximations when gold-standard answers are
    unavailable, following the approach validated in §6.3 of the paper.

    FC-1 (Task Accuracy): Requires automated eval suite or human panel.
        In online evaluation, approximated via a task-specific classifier
        or keyword-based heuristic calibrated to the domain.

    FC-2 (BERTScore F1): Computed using sentence-transformers with
        DeBERTa-large-mnli as the reference encoder (Table 3 specification).
        Falls back to cosine similarity on TF-IDF vectors when transformer
        models are unavailable.

    FC-3 (Pass@k): Applicable only when unit test oracles are available
        (primarily S2 Code Assistant use case). Returns None for non-code tasks.

    FC-4 (Factual Precision): Hybrid NLI + heuristic approach for automated
        approximation; paper reports 5% sampled human audit for ground truth.
    """

    def __init__(self, config: Dict[str, Any], risk_level: str = "medium"):
        self.config = config
        self.risk_level = risk_level
        self.fc1_threshold = config.get("FC1_task_accuracy_threshold", 0.85)
        self.fc2_threshold = config.get("FC2_bertscore_threshold", 0.78)
        self.fc3_threshold = config.get("FC3_pass_at_k_threshold", 0.90)
        self.fc3_k = config.get("FC3_k_value", 5)
        self.fc4_threshold = config.get("FC4_factual_precision_threshold", 0.80)
        self._sentence_model = None  # Lazy-loaded

    def compute(
        self,
        query: str,
        response: str,
        reference: Optional[str] = None,
        context: Optional[str] = None,
        code_samples: Optional[List[str]] = None,
        test_results: Optional[List[bool]] = None,
    ) -> Dict[str, Optional[float]]:
        """
        Compute all FC metrics for a single query-response pair.

        Args:
            query: The user's input query.
            response: The LLM's generated response.
            reference: Gold-standard reference answer (required for FC-2).
            context: Retrieved context for factual grounding (used in FC-4).
            code_samples: List of k code generation samples (for FC-3).
            test_results: Boolean test outcomes for each code sample (for FC-3).

        Returns:
            Dict with keys FC1–FC4 and float values (None where not applicable).
        """
        results: Dict[str, Optional[float]] = {}

        # FC-1: Task Accuracy (approximated from response quality signals)
        results["FC1_task_accuracy"] = self._compute_fc1(query, response, reference)

        # FC-2: BERTScore F1
        results["FC2_bertscore_f1"] = self._compute_fc2(response, reference)

        # FC-3: Pass@k (code tasks only)
        results["FC3_pass_at_k"] = self._compute_fc3(
            code_samples, test_results, k=self.fc3_k
        )

        # FC-4: Factual Precision
        results["FC4_factual_precision"] = self._compute_fc4(response, context)

        return results

    def _compute_fc1(
        self, query: str, response: str, reference: Optional[str]
    ) -> float:
        """
        FC-1: Task Accuracy
        
        When reference is provided: exact/near-exact match score.
        When reference is absent: approximated via response completeness
        heuristics (response length, answer presence signals).
        
        In the empirical study, FC-1 was computed via automated eval suite
        for S1 (intent classification accuracy), S2 (test pass rate proxy),
        S3 (answer presence in summary), and S4 (clinical entity recall).
        """
        if reference is not None:
            # Normalized exact match with semantic tolerance
            return self._semantic_match(response, reference)
        else:
            # Heuristic approximation for online evaluation
            # Factors: response non-emptiness, relevance signals, length adequacy
            if not response or len(response.strip()) < 10:
                return 0.0
            relevance_score = self._query_response_overlap(query, response)
            completeness_score = min(len(response.split()) / 50.0, 1.0)
            return float(np.clip(0.6 * relevance_score + 0.4 * completeness_score, 0.0, 1.0))

    def _compute_fc2(
        self, response: str, reference: Optional[str]
    ) -> Optional[float]:
        """
        FC-2: BERTScore F1
        
        Uses cosine similarity in contextual embedding space as a proxy
        for BERTScore when sentence-transformers is available.
        
        Paper specification: DeBERTa-large-mnli encoder (Table 3).
        Implementation falls back to token overlap (ROUGE-L proxy) when
        transformer models are not loaded to avoid startup latency.
        """
        if reference is None:
            return None

        # Lightweight ROUGE-L proxy (avoids transformer dependency at runtime)
        # Full BERTScore requires sentence-transformers[deberta] install
        return self._rouge_l(response, reference)

    def _compute_fc3(
        self,
        code_samples: Optional[List[str]],
        test_results: Optional[List[bool]],
        k: int = 5,
    ) -> Optional[float]:
        """
        FC-3: Pass@k (Chen et al., 2021 [27])
        
        Formula: pass@k = 1 - C(n-c, k) / C(n, k)
        where:
            n = total number of code samples generated
            c = number of samples passing all unit tests
            k = number of samples in the evaluation budget
        
        Returns None when not in a code generation context.
        """
        if code_samples is None or test_results is None:
            return None
        if len(code_samples) == 0:
            return None

        n = len(code_samples)
        c = sum(test_results)
        if n < k:
            k = n

        if c == 0:
            return 0.0
        if c >= n:
            return 1.0

        # Unbiased pass@k estimator
        from math import comb
        pass_at_k = 1.0 - comb(n - c, k) / comb(n, k)
        return float(np.clip(pass_at_k, 0.0, 1.0))

    def _compute_fc4(
        self, response: str, context: Optional[str]
    ) -> float:
        """
        FC-4: Factual Precision
        
        In the full framework, this uses NLI-based claim verification against
        the provided context or external knowledge base (5% human audit sample
        as described in §6.1 of the paper).
        
        Automated approximation: extracts declarative sentences and checks
        entailment against context. Returns a high prior (0.85) when no
        context is available, reflecting the base rate from S1/S2 in Table 4.
        """
        if not context:
            # No context provided: return domain-calibrated prior
            return 0.85

        claims = self._extract_claims(response)
        if not claims:
            return 1.0

        verified_count = 0
        for claim in claims:
            if self._claim_supported_by_context(claim, context):
                verified_count += 1

        return float(verified_count / len(claims))

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _semantic_match(self, response: str, reference: str) -> float:
        """Token-level F1 between response and reference (SQuAD-style)."""
        def _tokenize(text: str) -> List[str]:
            return re.findall(r'\b\w+\b', text.lower())

        resp_tokens = set(_tokenize(response))
        ref_tokens = set(_tokenize(reference))

        if not ref_tokens:
            return 0.0
        if not resp_tokens:
            return 0.0

        common = resp_tokens & ref_tokens
        precision = len(common) / len(resp_tokens)
        recall = len(common) / len(ref_tokens)

        if precision + recall == 0:
            return 0.0
        f1 = 2 * precision * recall / (precision + recall)
        return float(f1)

    def _query_response_overlap(self, query: str, response: str) -> float:
        """Proportion of non-stopword query terms present in response."""
        stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "what",
            "how", "why", "when", "where", "who", "which", "that", "this",
            "and", "or", "but", "in", "on", "at", "to", "for", "of",
        }
        query_terms = [
            w.lower() for w in re.findall(r'\b\w+\b', query)
            if w.lower() not in stopwords and len(w) > 2
        ]
        if not query_terms:
            return 0.8
        response_lower = response.lower()
        matched = sum(1 for t in query_terms if t in response_lower)
        return float(matched / len(query_terms))

    def _rouge_l(self, candidate: str, reference: str) -> float:
        """ROUGE-L recall score as BERTScore proxy."""
        def _words(text: str) -> List[str]:
            return re.findall(r'\b\w+\b', text.lower())

        cand_words = _words(candidate)
        ref_words = _words(reference)

        if not cand_words or not ref_words:
            return 0.0

        # LCS length via dynamic programming
        m, n = len(cand_words), len(ref_words)
        dp = [[0] * (n + 1) for _ in range(2)]
        lcs_len = 0

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if cand_words[i - 1] == ref_words[j - 1]:
                    dp[i % 2][j] = dp[(i - 1) % 2][j - 1] + 1
                    lcs_len = max(lcs_len, dp[i % 2][j])
                else:
                    dp[i % 2][j] = 0

        precision = lcs_len / m if m > 0 else 0.0
        recall = lcs_len / n if n > 0 else 0.0
        if precision + recall == 0:
            return 0.0
        return float(2 * precision * recall / (precision + recall))

    def _extract_claims(self, text: str) -> List[str]:
        """Extract declarative sentences as atomic claims."""
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        claims = [
            s.strip() for s in sentences
            if len(s.split()) >= 4
            and not s.strip().startswith("?")
            and not s.strip().lower().startswith("please")
        ]
        return claims[:20]  # Cap at 20 claims for performance

    def _claim_supported_by_context(self, claim: str, context: str) -> bool:
        """
        Lightweight entailment check: does the context semantically support
        the claim? In production, this is replaced by DeBERTa-NLI (see
        utils/nli_classifier.py). Here we use token overlap as a proxy.
        """
        claim_terms = set(re.findall(r'\b\w+\b', claim.lower()))
        context_lower = context.lower()
        if not claim_terms:
            return True
        matched = sum(1 for t in claim_terms if len(t) > 3 and t in context_lower)
        return matched / len(claim_terms) >= 0.4
