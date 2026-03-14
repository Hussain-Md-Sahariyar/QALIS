# IRB Approval Summary

**IRB reference**: QUATIC-2025-IRB-Annex-B  
**Study**: QALIS — Quality Assessment Framework for LLM-Integrated Software Systems  
**Status**: **Approved**  
**Approval date**: 26 September 2024  
**Expiry date**: 25 September 2025  

---

## Scope of Approval

The Institutional Review Board approved the following activities:

1. **Practitioner interviews** (n = 14)
   - Recruitment via professional networks and research contacts
   - Audio-recorded semi-structured video interviews (50–80 min)
   - Verbal and written informed consent
   - Storage and analysis of anonymised transcripts

2. **Case system metric collection** (S1–S4)
   - Collection of production metric data under system operator data use agreements
   - PII scrubbing of query logs before archiving
   - No direct data collection from end users of the case systems

3. **Human annotation panels**
   - FC-4 Factual Precision annotation (800 items, 3 annotators)
   - TI-2 Explanation Faithfulness annotation (500 items, 3 annotators)
   - TI-3 User Interpretability survey (14 practitioner participants)

---

## Risk Classification

**Risk level**: Minimal risk

Justification:
- No direct data collection from members of the public
- Interview participants are industry professionals with relevant expertise
- No sensitive personal health, financial, or legal data collected from participants
- All query log data PII-scrubbed before analysis
- No deception involved

---

## Conditions of Approval

The following conditions were attached to IRB approval:

1. Signed (or verbally recorded) informed consent obtained from all interview participants
2. Audio recordings deleted within 14 days of verified transcription
3. Transcripts anonymised before sharing with co-investigators
4. Red-team attack payloads stored in obfuscated/parameterised form only;
   verbatim payloads not included in public repository
5. Inclusion of this IRB reference in all publications arising from the study
6. Annual progress report to the IRB (or on study completion)

---

## Notes for Reviewers

The full IRB application, including the study protocol, consent form templates,
data management plan, and data use agreements with case system operators, is
available to reviewers on request.

Contact the corresponding author (identity withheld for double-blind review).
IRB documentation will be disclosed on paper acceptance.

---

*This summary is provided for transparency. The IRB reference number
(QUATIC-2025-IRB-Annex-B) is cited in `configs/red_team_config.yaml` and
throughout the paper where human subjects research is described.*
