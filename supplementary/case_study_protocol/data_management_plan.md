# Data Management Plan

**Study**: QALIS — Quality Assessment Framework for LLM-Integrated Software Systems  
**IRB reference**: QUATIC-2025-IRB-Annex-B  
**Version**: 1.0 | **Date**: September 2024  

---

## 1. Data Types Collected

| Data type | Source | Format | Identifiable? |
|-----------|--------|--------|---------------|
| Real-time metric snapshots | Production systems S1–S4 | CSV.gz | No |
| Query/response logs | Production systems S1–S4 | JSONL.gz | Partially* |
| Practitioner interview audio | 14 interviews | MP4 | Yes |
| Practitioner interview transcripts | Transcription of audio | TXT | Yes → anonymised |
| Human annotation panel data | Research team | CSV | No |
| Red-team corpus | Research team | CSV.gz | No |
| Perturbation test datasets | Automated generation | CSV | No |

*Query logs may contain personally identifiable information (PII) in user queries.
All logs were PII-scrubbed using the SS-2 PII detector before archiving
(see `configs/qalis_config.yaml > anonymisation`).

---

## 2. Data Storage and Access

### 2.1 During the Study

- Metric and log data: encrypted at rest on institutional compute cluster
- Audio recordings: stored in encrypted folder accessible to PI only
- Transcripts (pre-anonymisation): PI-access only encrypted storage
- All research data: institutional VPN required for remote access

### 2.2 After Anonymisation

- Anonymised transcripts: shared with co-investigators for analysis
- Coded excerpts: stored in `interviews/` directory (included in this repository)
- Quantitative data: stored in `data/` directory (included in this repository)

### 2.3 Public Repository (This Repository)

The following data is included in this public repository:

**Included**:
- Anonymised metric data (system IDs S1–S4; no user PII)
- Anonymised coded interview excerpts and thematic analysis
- Perturbation test datasets (automatically generated)
- Red-team corpus (obfuscated/parameterised payloads only)
- Analysis scripts and configuration files

**Excluded** (retained securely, available to reviewers on request):
- Raw audio recordings (deleted after transcription)
- Pre-anonymisation transcripts
- Signed consent forms
- Full verbatim interview transcripts (available to reviewers under NDA)

---

## 3. Anonymisation Procedure

### Metric and Log Data
- System names replaced with S1–S4 codes before archiving
- User PII in query text detected and replaced with `[REDACTED_PII]` by the
  SS-2 PII detector (see `src/qalis/metrics/safety_security.py`)
- Vendor and product names not included in archived logs

### Interview Data
Step 1: Automated PII detection removes names, email addresses, and phone numbers.  
Step 2: Manual review replaces organisation names with sector descriptors
  (e.g. "a major UK retail bank" → "large financial services firm").  
Step 3: Product names, LLM vendor names in context, and project-specific terms replaced.  
Step 4: Co-investigator review before archiving coded excerpts.

---

## 4. Retention and Deletion

| Data type | Retention period | Deletion method |
|-----------|-----------------|-----------------|
| Audio recordings | Until transcript verified (≤14 days) | Secure overwrite |
| Pre-anonymisation transcripts | 5 years post-publication | Secure overwrite |
| Signed consent forms | 5 years post-publication | Secure shredding |
| Anonymised quantitative data | Indefinite (open data) | N/A |
| Anonymised qualitative data | Indefinite (open data) | N/A |

---

## 5. Data Sharing

The anonymised dataset included in this repository is released under the
**Creative Commons Attribution 4.0 International (CC BY 4.0)** licence.
Attribution: [Author names withheld for review].

Reviewers requiring access to non-public data (full transcripts, signed consent forms)
should contact the corresponding author. Access is granted under NDA, subject to
IRB approval.

---

## 6. Compliance

- EU GDPR (Regulation 2016/679) — applicable to interview participants in Europe
- HIPAA not directly applicable (no patient data collected; S4 data is synthetic/anonymised)
- Institutional data governance policy: compliant
- IRB approval: QUATIC-2025-IRB-Annex-B
