# AI / LLM Application Security

## Scope

Apply normal application security to LLM/agent systems, plus model/data/tool-specific controls. Prompt text is not a security boundary.

## Rules

### AI-001 Untrusted prompt/content controls policy
Report architectures where external/retrieved content can override security policy and trigger privileged effects without independent enforcement.

### AI-002 Tool call lacks independent authorization
HIGH when a model invokes privileged tools and the tool trusts model decisions without validating principal, authorization, operation, arguments, scope, and resource/cost limits.

The model may propose an action; deterministic code should enforce permissions/invariants.

### AI-003 Excessive tool privileges
Report filesystem, shell, network, database, cloud, or connector access broader than the task requires. Prefer scoped roots/resources and allowlists.

### AI-004 Unsafe model output execution
Report direct execution/evaluation of model-generated shell, SQL, code, templates, URLs, or filesystem paths without validation/sandboxing/parameterization.

### AI-005 Sensitive data leakage
Review prompts, retrieved docs, tool outputs, traces, eval artifacts, and telemetry for secrets/PII/proprietary data sent to unauthorized destinations or retained improperly.

### AI-006 RAG trust/provenance failure
Retrieved content is untrusted unless controlled/validated. Keep provenance, separate instructions from retrieved data, enforce access control before retrieval, and constrain side effects.

### AI-007 Cross-user/tenant memory leakage
HIGH when memory, embeddings, caches, vector stores, traces, or conversation state can expose one user's/tenant's data to another.

### AI-008 Missing loop/resource limits
Bound steps, retries, tool calls, recursion, token/cost use, and dangerous repeated actions according to risk.

### AI-009 Untrusted tool/MCP capability
Treat external tool servers/connectors as privileged dependencies. Review server trust, credential scope, arguments, data disclosure, and high-impact action controls.

### AI-010 LLM output confused with verified fact
For security/high-impact operations, do not treat free-form model output as authoritative verification. Prefer structured output, deterministic validation, provenance, and explicit failure handling.

## False positives

Do not classify:
- LLM token-count logic as authentication-token weakness;
- prompts containing password/SECRET_KEY/admin words as active secrets;
- evaluator fixtures/security examples as vulnerabilities without a production execution path.
