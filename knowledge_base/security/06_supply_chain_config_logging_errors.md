# Supply Chain, Configuration, Logging, and Error Handling

## Supply chain

### SUPPLY-001 Uncontrolled dependency acquisition
Report executable dependencies/scripts fetched from mutable or unverified sources, risky ambiguous package sources, or disabled integrity checks where provenance matters.

### SUPPLY-002 Unsafe CI/CD trust boundary
Review untrusted PR/fork code receiving secrets, excessive runner permissions, broad deployment credentials, mutable unreviewed build actions, and artifact-integrity gaps.

### SUPPLY-003 Vulnerable dependency handling
Prefer SCA/dependency tools for CVEs. Report clear evidence that vulnerability management is disabled/ignored or critical vulnerabilities are deliberately retained without mitigation.

## Configuration

### CONFIG-001 Debug mode in production
Report only when runtime/deployment enables debug in production or another sensitive environment.

Do not report logger debug calls, rule definitions, tests, or detector signatures.

### CONFIG-002 Insecure default exposure
Report production-relevant insecure defaults such as anonymous/admin access, permissive sensitive CORS, disabled TLS/certificate verification, disabled auth, or default credentials.

### CONFIG-003 Environment separation failure
Report meaningful mixing of development/test and production secrets, endpoints, data, privileges, or debug controls.

## Logging

### LOG-001 Sensitive data in logs
Do not log passwords, private keys, bearer/session tokens, or unnecessary sensitive data. Use redaction/masking.

### LOG-002 Missing security-event visibility
Important systems should make authentication failures, authorization violations, suspicious session/token failures, privileged operations, and material security configuration changes observable.

### LOG-003 Log injection/integrity
Untrusted values must not forge records or manipulate downstream parsing; protect logs according to risk.

## Error handling

### ERR-001 Sensitive diagnostics exposed
Report external stack traces, secrets, sensitive paths/query data, internal exception objects, or materially useful infrastructure details.

### ERR-002 Security fail-open
HIGH when authentication, authorization, validation, signature verification, or another control grants access after exception/timeout/unknown state.

### ERR-003 Unbounded retry/error loop
Report retry behavior that can materially amplify cost/load or cause cascading failure.

## Common CWE mappings

- CWE-209 information exposure through error message
- CWE-532 sensitive information in logs
- CWE-117 log output neutralization
