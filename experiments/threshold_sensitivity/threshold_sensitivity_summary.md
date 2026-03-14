# Threshold Sensitivity Analysis Summary

## SF-3 Sweep (exp_thr_001)

Default threshold of 2.0 hallucinations/1K tokens is near-optimal by F1.
Clinical domain override to 1.0 is justified — catches 3 additional real
incidents per month that the default threshold misses, at cost of +2.1 pp
false positive rate.

## RO-2 Sweep (exp_thr_002)

Default threshold of 0.97 injection resistance rate is near-optimal.
Clinical domain override to 0.99 justified for S4 given patient safety stakes.

## Domain Override Impact (exp_thr_003)

All five domain overrides tested are justified:

| System | Metric | Override | Incidents Caught | Verdict |
|--------|--------|----------|-----------------|---------|
| S4 | SF-3 | 2.0 → 1.0 | +3/month | ✓ Clinical safety |
| S4 | SS-2 | 0.001 → 0.0001 | +2/month | ✓ HIPAA compliance |
| S4 | TI-1 | 0.70 → 0.95 | +6/month | ✓ EU AI Act |
| S2 | IQ-2 | 2500 → 1500ms | Corr. with UX | ✓ IDE responsiveness |
| S3 | SS-2 | 0.001 → 0.0005 | +1/month | ✓ GDPR |

**Conclusion**: Default thresholds are appropriate for general deployment.
Domain overrides should be applied for regulated or high-risk contexts.
