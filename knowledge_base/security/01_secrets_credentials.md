# Secrets and Credentials

## Objective

Credentials and cryptographic secrets must not be exposed in source, logs, build artifacts, client bundles, error responses, or broadly accessible configuration. Access should be least-privileged, auditable, revocable, and rotatable.

## Rules

### SEC-SECRET-001 Hardcoded production secret
Report a literal/embedded usable API key, DB password, cloud credential, OAuth client secret, signing/encryption key, private key, service-account credential, or privileged token when production relevance is credible.

Severity:
- CRITICAL for active broad-privilege production secrets/private keys;
- HIGH for material narrower credentials;
- lower only when context justifies it.

Do not report from names alone.

### SEC-SECRET-002 Secret in client-delivered code
Report server-side secrets embedded in browser/mobile/public client bundles.

### SEC-SECRET-003 Secret logging
Report passwords, private keys, bearer/session tokens, sensitive connection strings, or equivalent credentials written to logs/traces/analytics/exceptions.

### SEC-SECRET-004 Over-broad secret access
Report wildcard/broad secret access, shared admin credentials, or CI/CD secret exposure beyond least privilege.

### SEC-SECRET-005 Missing rotation/revocation
Report when a high-impact long-lived secret clearly lacks a feasible rotation/revocation model.

## Preferred controls

- managed secret stores;
- workload identity/short-lived credentials;
- least-privilege IAM;
- automated rotation where feasible;
- separate credentials by service/environment;
- redaction/masking in logs.

Environment variables are a transport mechanism, not automatically a complete secret-management system.

## If a secret was committed

1. revoke/rotate;
2. assess exposure/use;
3. remove/replace;
4. prevent recurrence with secret scanning and protected CI/CD;
5. handle repository-history exposure according to incident policy.

## Common CWE mappings

- CWE-798 hardcoded credentials
- CWE-259 hardcoded password
- CWE-200 sensitive-information exposure
