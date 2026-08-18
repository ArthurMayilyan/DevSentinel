# AgentLoop Production Security Knowledge Base

Version: 2026-08-18

Purpose: compact, code-review-oriented security guidance for AgentLoop RAG/OpenAI-assisted review.

Primary baseline:
- OWASP ASVS 5.0.0 (stable)
- OWASP Top 10:2025
- OWASP API Security Top 10:2023
- OWASP Cheat Sheet Series
- NIST SP 800-218 SSDF 1.1 (final)
- NIST SP 800-218A for generative-AI software development (final)
- NIST SP 800-218 Rev.1 / SSDF 1.2 is draft and is informative only

Use these documents as contextual evidence. A deterministic pattern-only reviewer will not become context-aware merely because the KB is present.

Review principles:
1. Require concrete code/config evidence.
2. Distinguish production execution paths from tests, fixtures, examples, detector signatures, and documentation.
3. Do not report a vulnerability from a keyword alone.
4. Identify asset, source, dangerous operation/control, missing protection, and reachability.
5. Treat a committed real secret as exposed even if later removed.
6. Do not confuse NLP/LLM tokens with authentication/session tokens.

Severity baseline:
- CRITICAL: directly exploitable broad compromise, active high-privilege production credential, unauthenticated admin, clear RCE.
- HIGH: material authorization/authentication bypass, powerful injection, sensitive-data compromise, unsafe security-token validation.
- MEDIUM: meaningful defense-in-depth or hardening failure with limited/preconditioned impact.
- LOW: minor hardening issue.

Files:
- 00_review_policy.md
- 01_secrets_credentials.md
- 02_authentication_sessions_tokens.md
- 03_authorization_access_control.md
- 04_input_injection_ssrf_files.md
- 05_api_data_crypto.md
- 06_supply_chain_config_logging_errors.md
- 07_ai_llm_security.md

Review this KB quarterly and when the underlying standards materially change.

This is a security-review baseline, not a substitute for threat modeling, architecture review, SAST/DAST/SCA, penetration testing, incident response, or compliance requirements.
