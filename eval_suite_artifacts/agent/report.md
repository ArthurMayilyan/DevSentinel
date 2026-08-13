# RAG Agent Eval Report

## Configuration

Knowledge path: `./knowledge_base_noisy`
Cases path: `./eval_cases/rag_agent_eval_cases.json`
Strategy: `binary-overlap`
Max steps: `4`
Min agent answer accuracy: `1.0`

## Summary

Agent answer accuracy: **1.00**
Passed cases: **2**
Failed cases: **0**

## Cases

| Case | Passed | search_knowledge called | Failures |
|---|---:|---:|---|
| agent token expiration answer | true | true |  |
| agent small function answer | true | true |  |