# API Security, Sensitive Data, and Cryptography

## API rules

### API-001 Excessive property/data exposure
Report responses exposing sensitive/internal fields not required by the caller. Prefer explicit response schemas/DTOs.

### API-002 Unrestricted resource consumption
Report meaningful DoS/cost-amplification from unbounded pagination, uploads, query complexity, exports, concurrency, CPU/memory work, or paid downstream calls.

Use quotas, rate limits, timeouts, size limits, and bounded pagination.

### API-003 Sensitive business-flow abuse
Review automation/abuse controls for high-value flows such as scarce purchases, account creation, password reset, promotions, messaging, or expensive computations.

### API-004 Unsafe third-party API consumption
Treat third-party responses as untrusted. Validate data/schema, authenticate endpoints, constrain redirects/timeouts/response sizes, and avoid blindly forwarding errors/content.

### API-005 Forgotten/deprecated endpoint exposure
Report debug/admin/legacy API versions that remain reachable without expected controls.

## Sensitive data

### DATA-001 Sensitive data exposure
Report secrets, credentials, private personal data, or sensitive business data exposed to unauthorized users, logs, traces, public storage, or client responses.

### DATA-002 Missing transport protection
Report sensitive production communication over insecure transport when authenticated encryption is required.

### DATA-003 Insecure storage protection
Report sensitive data stored without required encryption/access protection when threat model/policy requires it. Do not demand application-layer encryption for every field without context.

## Cryptography

### CRYPTO-001 Broken/deprecated primitive
Report algorithms unsuitable for the stated security purpose.

### CRYPTO-002 Poor key management
Apply the secrets rules to cryptographic keys.

### CRYPTO-003 Insecure randomness
Report predictable randomness for passwords, reset/session tokens, API keys, CSRF secrets, nonces, or other security-sensitive values.

### CRYPTO-004 Home-grown cryptographic protocol
Strongly scrutinize custom signing/encryption/token schemes; prefer established reviewed protocols/libraries.

## False positives

- A hash can be fine for a non-security checksum but unsuitable for password storage.
- Simulation/UI randomness is not security randomness.
- Base64 is encoding, not encryption, but only report when code relies on it for confidentiality/security.

## Common CWE mappings

- CWE-200 sensitive-information exposure
- CWE-327 risky/broken crypto algorithm
- CWE-330 insufficient randomness
- CWE-319 cleartext transmission of sensitive information
