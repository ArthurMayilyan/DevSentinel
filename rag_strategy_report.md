# RAG Strategy Comparison Report

## Summary

| Strategy | Hit rate | Top-1 accuracy | MRR |
|---|---:|---:|---:|
| term-frequency | 1.00 | 0.00 | 0.50 |
| binary-overlap | 1.00 | 1.00 | 1.00 |
| hybrid-lexical | 1.00 | 1.00 | 1.00 |

Best strategy: **binary-overlap**

Best strategy metrics: MRR=1.00, Top-1=1.00, Hit rate=1.00

## Baseline

Baseline strategy: **term-frequency**

## Strategy diagnostics vs baseline

### binary-overlap

Improved: **2**, regressed: **0**, unchanged: **0**

Improved cases:

- token expiration policy: rank 2 → 1
- small function guideline: rank 2 → 1

### hybrid-lexical

Improved: **2**, regressed: **0**, unchanged: **0**

Improved cases:

- token expiration policy: rank 2 → 1
- small function guideline: rank 2 → 1

## Candidate decisions

| Candidate | Accepted | Improved | Regressed | Reasons |
|---|---:|---:|---:|---|
| binary-overlap | true | 2 | 0 |  |
| hybrid-lexical | true | 2 | 0 |  |

Best accepted strategy: **binary-overlap**

## Regression gate

Max regressed cases: **0**  Total regressed cases: **0**  Passed: **true**

## Improvement gate

Min improved cases: **1**  Total improved cases: **4**  Passed: **true**

## Quality gate

Passed: **true**
