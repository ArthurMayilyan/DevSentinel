# RAG Strategy Comparison Report

## Run metadata

Created at UTC: `2026-08-12T13:09:27.415234+00:00`
Knowledge path: `./knowledge_base_noisy`
Cases path: `./eval_cases/noisy_rag_eval_cases.json`
Top K: `3`
Strategies: `term-frequency,binary-overlap,hybrid-lexical`
Baseline strategy: `term-frequency`
Max regressed cases: `0`
Min improved cases: `1`

## Input fingerprints

### Knowledge files

| Relative path | Size bytes | SHA256 |
|---|---:|---|
| coding.md | 163 | `fad39bb121f5e9ad24c5f6c400a36326effa25aea6d45f76a6dafd602ec86779` |
| noise_functions.md | 73 | `d2a0efc3016533e1a492fa5d732b459ec7f1b8ed5b377c92c98cc80a0cc14a2e` |
| noise_tokens.md | 64 | `c1c68a23229d534e8b98d78fd7b7f5565462e026fdb4ba311a906e278b9bce0c` |
| security.md | 177 | `83d5b1a52d594670db8909bce1230c41efc8218ad35733d2733c13a5d57cf566` |

### Case files

| Relative path | Size bytes | SHA256 |
|---|---:|---|
| noisy_rag_eval_cases.json | 386 | `95bf3ebe7e9791b5a76b58f8b62b4e0f2925c7da950cf9df457697b8386c5909` |

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
