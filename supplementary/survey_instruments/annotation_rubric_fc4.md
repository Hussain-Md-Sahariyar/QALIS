# FC-4 Factual Precision — Annotation Rubric

**Metric**: FC-4 Factual Precision  
**Formula**: `correct_claims / total_verifiable_claims`  
**Threshold**: ≥ 0.78  
**IAA achieved**: Fleiss κ = 0.76 (target: κ ≥ 0.70 ✓)  
**Paper reference**: §4.2, Table 3; §3.5 (annotation protocol)

---

## Decision Tree

```
Is the claim verifiable using the provided context?
│
├── NO  → Label: UNVERIFIABLE
│         (no penalty to FC-4 score; excluded from denominator)
│
└── YES → Does the claim match or follow from the context?
          │
          ├── YES → Label: CORRECT   (counts toward numerator)
          │
          └── NO  → Label: INCORRECT (reduces FC-4 score)
```

---

## Detailed Label Definitions

### CORRECT

A claim is CORRECT if it satisfies **all three** conditions:

1. It is **supported by evidence** present in the provided context, OR it is
   well-established common knowledge (e.g. physical constants, basic geography)
2. It is **factually accurate** — numbers, dates, names, policy terms match exactly
   or are valid paraphrases that preserve meaning
3. It does **not introduce information** not present in the context that changes the
   implication of the claim

**Edge cases**:
- Rounding: "approximately 30%" when context says "29.8%" → CORRECT
- Paraphrase: "returned within a month" when context says "30 days" → CORRECT
- Generalisation: "most patients respond" when context says "72% respond" → CORRECT

---

### INCORRECT

A claim is INCORRECT if it satisfies **any one** of:

1. It **contradicts the context** — a number, date, name, or fact is wrong
2. It is a **hallucination** — it presents information as fact that does not appear
   in the context and is not common knowledge
3. It **overstates certainty** — e.g. "the patient has X" when context says "consistent with X"

**Edge cases**:
- Wrong direction: "more than 30 days" when context says "within 30 days" → INCORRECT
- Fabricated citation: "According to NICE guideline CG123" when no guideline cited in context → INCORRECT
- Mixed correct/incorrect: if the claim contains both correct and incorrect parts,
  label the **most specific factual element** as the target

---

### UNVERIFIABLE

A claim is UNVERIFIABLE if:

1. **No relevant context** was provided for this query type
2. The claim concerns external facts, industry standards, or general knowledge that
   the provided context does not address
3. The context is **ambiguous** and neither clearly supports nor refutes the claim
4. The claim is **speculative** or probability-framed without a verifiable ground truth

Note: UNVERIFIABLE is NOT a negative label. It means the claim is outside the scope
of what this metric can assess.

---

## Confidence Scale

| Score | Meaning | When to use |
|-------|---------|-------------|
| 1 | Very uncertain | I am guessing; the evidence is unclear |
| 2 | Uncertain | I lean toward a label but have significant doubts |
| 3 | Moderately confident | I believe my label is correct but some ambiguity remains |
| 4 | Confident | My label is well-supported; minor doubts only |
| 5 | Certain | The evidence clearly and unambiguously supports my label |

Items with average annotator confidence < 3 are flagged for senior review.

---

## Domain-Specific Notes

**S1 (Customer Support)**: Context is usually policy documents or FAQs. Dates,
numbers, and policy terms are common sources of incorrect claims.

**S2 (Code Assistant)**: Claims about code behaviour (e.g. "this function returns null
if X") can be verified by reading the provided code snippet. Technical correctness
is the focus.

**S3 (Document QA)**: Context is document excerpts. Claims must be traceable to the
excerpt — not to general knowledge about the topic.

**S4 (Medical Triage)**: Clinical claims require care. Use UNVERIFIABLE if no clinical
guideline or patient data was provided. Never use your own medical knowledge to
adjudicate — only the provided context counts.

---

## Inter-Annotator Agreement Target

**Fleiss κ ≥ 0.70** (substantial agreement per Landis & Koch, 1977).
Achieved in this study: **κ = 0.76**.
