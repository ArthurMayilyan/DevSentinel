# RAG Answer Eval Report

## Configuration

Knowledge path: `./knowledge_base_noisy`
Cases path: `./eval_cases/rag_answer_eval_cases.json`
Top K: `1`
Strategy: `binary-overlap`
Min answer accuracy: `1.0`

## Summary

Total cases: **2**
Passed cases: **2**
Failed cases: **0**
Answer accuracy: **1.00**

## Quality gate

Passed: **true**

## Cases

| Case | Passed | Expected answer text | Expected source | Failure reasons |
|---|---:|---|---|---|
| token expiration answer | true | Token expiration policy | security.md |  |
| small function answer | true | Small function guidelines | coding.md |  |
