# RAG Agent Run Report

## Configuration

Knowledge path: `./knowledge_base_noisy`
Strategy: `binary-overlap`
LLM: `deterministic`
Model: `gpt-5`
Max steps: `4`

## Query

How should credentials and debug mode be handled in production?

## Answer

Credentials must not be hardcoded in source code.
Debug mode must be disabled in production.

Source: knowledge_base_noisy\security.md

## Sources

- `knowledge_base_noisy\security.md`

## Guardrail

Guardrail passed: `None`
Fallback used: `False`

Failure reasons: none

## Evidence

### Evidence 1

Source: `knowledge_base_noisy\security.md`

# Security Policy

Token expiration policy: tokens must be signed and must expire.
Credentials must not be hardcoded in source code.
Debug mode must be disabled in production.


## Trace

Trace steps: `3`