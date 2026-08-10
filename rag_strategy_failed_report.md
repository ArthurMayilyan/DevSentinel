# RAG Strategy Comparison Report

## Summary

| Strategy | Hit rate | Top-1 accuracy | MRR |
|---|---:|---:|---:|
| binary-overlap | 1.00 | 1.00 | 1.00 |
| hybrid-lexical | 1.00 | 1.00 | 1.00 |
| term-frequency | 1.00 | 0.00 | 0.50 |

Best strategy: **binary-overlap**

Best strategy metrics: MRR=1.00, Top-1=1.00, Hit rate=1.00

## Baseline

Baseline strategy: **binary-overlap**

## Strategy diagnostics vs baseline

### hybrid-lexical

Improved: **0**, regressed: **0**, unchanged: **2**

### term-frequency

Improved: **0**, regressed: **2**, unchanged: **0**

Regressed cases:

- token expiration policy: rank 1 → 2
- small function guideline: rank 1 → 2

## Candidate decisions

| Candidate | Accepted | Improved | Regressed | Reasons |
|---|---:|---:|---:|---|
| hybrid-lexical | false | 0 | 0 | insufficient_improvements |
| term-frequency | false | 0 | 2 | too_many_regressions,insufficient_improvements |

Best accepted strategy: **<none>**

## Regression gate

Max regressed cases: **0**  Total regressed cases: **2**  Passed: **false**

## Improvement gate

Min improved cases: **1**  Total improved cases: **0**  Passed: **false**

## Quality gate

Passed: **false**
Failed gates: **regression,improvement**
