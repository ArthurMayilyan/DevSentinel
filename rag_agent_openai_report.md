# RAG Agent Run Report

## Configuration

Knowledge path: `./knowledge_base_noisy`
Strategy: `binary-overlap`
LLM: `openai`
Model: `gpt-5`
Max steps: `4`

## Query

token expiration

## Answer

Tokens must be signed and must expire. [Source: knowledge_base_noisy\security.md]

## Sources

- `knowledge_base_noisy\security.md`
- `knowledge_base_noisy\noise_tokens.md`

## Guardrail

Guardrail passed: `True`
Fallback used: `False`

Failure reasons: none

## Evidence

### Evidence 1

Source: `knowledge_base_noisy\security.md`

# Security Policy

Token expiration policy: tokens must be signed and must expire.
Credentials must not be hardcoded in source code.
Debug mode must be disabled in production.

### Evidence 2

Source: `knowledge_base_noisy\noise_tokens.md`

# Token Noise

token token token token token token token token


## Trace

Trace steps: `2`