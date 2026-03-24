# Paraphrase Invariance Tests (RO-4)

**4,000 paraphrase pairs** across 4 systems (1,000 per system), 4 methods.

## Files

| File | Description |
|------|-------------|
| `paraphrase_invariance_dataset.csv` | Full dataset — 4,000 rows |
| `paraphrase_summary_statistics.json` | Per-system statistics + SF-3 correlation note |
| `generate_paraphrase_tests.py` | Regeneration script |

## Schema

| Column | Type | Description |
|--------|------|-------------|
| `pair_id` | str | Unique identifier (PARA-NNNNN) |
| `system_id` | str | S1–S4 |
| `original_query` | str | Source query |
| `paraphrase_query` | str | Paraphrased version |
| `paraphrase_type` | str | Generation method |
| `original_output_embedding_norm` | float | Embedding magnitude of original response |
| `paraphrase_output_embedding_norm` | float | Embedding magnitude of paraphrased response |
| `cosine_similarity` | float | Similarity between response embeddings |
| `semantic_match` | int | 1 if cosine_similarity ≥ 0.75 |
| `factual_consistency` | int | NLI-verified factual consistency |
| `date_run` | date | Test execution date |

## Paraphrase methods

| Method | Weight | Description |
|--------|--------|-------------|
| `back_translation` | 40% | English → German → English |
| `lexical_substitution` | 30% | WordNet synonym replacement |
| `syntactic_transformation` | 20% | Active/passive, reordering |
| `human_paraphrase` | 10% | Crowdsourced (study onboarding) |

## RO-4 Threshold

**≥ 0.85** cosine similarity between response embeddings.

**Key finding**: RO-4 correlates with SF-3 (r = 0.61) — use as a real-time
hallucination proxy (Section 6.2, Figure 4).
