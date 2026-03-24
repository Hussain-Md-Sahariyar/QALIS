# TI-3 User Interpretability — Survey Instrument

**Metric**: TI-3 User Interpretability Score  
**Scale**: 1–5 Likert (1 = strongly disagree, 5 = strongly agree)  
**Threshold**: Raw score ≥ 3.5 / 5.0 (≡ normalised ≥ 6.25 / 10)  
**Reliability achieved**: Cronbach α = 0.84 (target: α ≥ 0.70 ✓)  
**Participants**: 14 (same cohort as practitioner interviews, Nov–Dec 2024)  
**Administration**: Online form, completed immediately after the interview  
**Paper reference**: §4.2, Table 3; §3.5 (TI-3 operationalisation)

---

## Preamble (shown to participants)

> The following questions ask about the **explainability and interpretability** of the
> AI system(s) you described during the interview. Please answer with reference to the
> **system you discussed most during the interview** (or your most recent or primary
> LLM-integrated system if you discussed several).
>
> There are no right or wrong answers — we are interested in your experience as a
> practitioner. All responses are anonymous and aggregated.
>
> Each statement is rated on a 5-point scale:
> **1 = Strongly disagree · 2 = Disagree · 3 = Neutral · 4 = Agree · 5 = Strongly agree**

---

## Section A: Output Interpretability

**TI3-A1**  
*"I can usually understand why the system produced a particular response."*

☐ 1 — Strongly disagree  
☐ 2 — Disagree  
☐ 3 — Neutral  
☐ 4 — Agree  
☐ 5 — Strongly agree  

---

**TI3-A2**  
*"The system's outputs include enough information for me to verify whether the response is correct."*

☐ 1 — Strongly disagree  
☐ 2 — Disagree  
☐ 3 — Neutral  
☐ 4 — Agree  
☐ 5 — Strongly agree  

---

**TI3-A3**  
*"When the system makes an error, I am typically able to identify why it occurred."*

☐ 1 — Strongly disagree  
☐ 2 — Disagree  
☐ 3 — Neutral  
☐ 4 — Agree  
☐ 5 — Strongly agree  

---

## Section B: Explanation Quality

**TI3-B1**  
*"When the system provides an explanation or reasoning, I find it helpful for understanding its output."*

☐ 1 — Strongly disagree  
☐ 2 — Disagree  
☐ 3 — Neutral  
☐ 4 — Agree  
☐ 5 — Strongly agree  
☐ N/A — My system does not provide explanations  

---

**TI3-B2**  
*"The system's explanations accurately reflect how it arrived at its answer (i.e. they are not misleading or post-hoc rationalisations)."*

☐ 1 — Strongly disagree  
☐ 2 — Disagree  
☐ 3 — Neutral  
☐ 4 — Agree  
☐ 5 — Strongly agree  
☐ N/A — My system does not provide explanations  

---

## Section C: Auditability

**TI3-C1**  
*"I am confident that my organisation could audit the system's outputs if required (e.g. for regulatory or compliance purposes)."*

☐ 1 — Strongly disagree  
☐ 2 — Disagree  
☐ 3 — Neutral  
☐ 4 — Agree  
☐ 5 — Strongly agree  

---

**TI3-C2**  
*"The system provides sufficient logging and traceability for me to reconstruct what happened in a past interaction."*

☐ 1 — Strongly disagree  
☐ 2 — Disagree  
☐ 3 — Neutral  
☐ 4 — Agree  
☐ 5 — Strongly agree  

---

## Section D: Confidence Communication

**TI3-D1**  
*"The system communicates its uncertainty or confidence level in a way I find useful."*

☐ 1 — Strongly disagree  
☐ 2 — Disagree  
☐ 3 — Neutral  
☐ 4 — Agree  
☐ 5 — Strongly agree  

---

**TI3-D2**  
*"I trust the system's confidence signals — when it expresses uncertainty, it is usually right to do so."*

☐ 1 — Strongly disagree  
☐ 2 — Disagree  
☐ 3 — Neutral  
☐ 4 — Agree  
☐ 5 — Strongly agree  

---

## Open-Ended Follow-Up

*(Optional — not scored; used for qualitative triangulation)*

**TI3-OE1**  
*"Is there anything about the interpretability or explainability of your system that you found particularly challenging or noteworthy?"*

[Free text field — no word limit]

---

## Scoring

TI-3 score is the **mean of all applicable Likert items** (N/A items excluded).

| Mean score | Normalised (0–10) | Interpretation |
|------------|------------------|----------------|
| 1.0 | 0.0 | Completely uninterpretable |
| 2.5 | 3.75 | Poor interpretability |
| 3.5 | 6.25 | **Threshold (≥ 3.5 to pass)** |
| 4.0 | 7.5 | Good interpretability |
| 5.0 | 10.0 | Fully interpretable |

**Study results by system** (mean across 14 participants):

| System | Mean TI-3 | Normalised | Passes threshold |
|--------|-----------|-----------|-----------------|
| S1 | 3.2 | 5.5 | ✗ (below 3.5) |
| S2 | 3.6 | 6.5 | ✓ |
| S3 | 4.1 | 7.75 | ✓ |
| S4 | 4.5 | 8.75 | ✓ |

*S1 (Customer Support) was the only system that did not meet the TI-3 threshold,
consistent with its overall TI dimension score of 5.6/10 (lowest across all systems
on this dimension). Paper §6.1 discusses actionable gaps in S1 transparency.*

---

## Reliability Analysis

Cronbach α = 0.84 computed across the 10 scored items (TI3-A1 through TI3-D2).

| Item | α if deleted | Item–total r |
|------|-------------|-------------|
| TI3-A1 | 0.82 | 0.71 |
| TI3-A2 | 0.83 | 0.65 |
| TI3-A3 | 0.81 | 0.73 |
| TI3-B1 | 0.84 | 0.58 |
| TI3-B2 | 0.82 | 0.69 |
| TI3-C1 | 0.80 | 0.78 |
| TI3-C2 | 0.81 | 0.75 |
| TI3-D1 | 0.83 | 0.62 |
| TI3-D2 | 0.84 | 0.55 |

All items retained (α if deleted ≤ current α; no items flagged for removal).

*Paper reference: §3.5 — "Cronbach's alpha for the TI-3 survey instrument was 0.84,
indicating good internal consistency (Nunnally, 1978)."*
