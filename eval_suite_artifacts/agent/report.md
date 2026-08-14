# RAG Agent Eval Report

## Configuration

Knowledge path: `./knowledge_base_noisy`
Cases path: `./eval_cases/rag_agent_eval_cases.json`
Strategy: `binary-overlap`
LLM: `deterministic`
Model: `gpt-5`
Max steps: `4`
Min agent answer accuracy: `1.0`

## Summary

Agent answer accuracy: **1.00**
Guardrail checked cases: **0**
Guardrail passed cases: **0**
Fallback used cases: **0**
Passed cases: **3**
Failed cases: **0**

## Cases

| Case | Passed | search_knowledge called | Guardrail passed | Fallback used | Failures |
|---|---:|---:|---:|---:|---|
| agent token expiration answer | true | true | none | false |  |
| agent small function answer | true | true | none | false |  |
| agent credentials and debug production answer | true | true | none | false |  |