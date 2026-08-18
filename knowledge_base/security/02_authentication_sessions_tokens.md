# Authentication, Sessions, and Security Tokens

## Objective

Authentication must establish identity with trustworthy authenticators. Session/token mechanisms must resist forgery, replay, prediction, fixation, theft, and indefinite reuse.

## Rules

### AUTH-001 Authentication bypass
HIGH/CRITICAL when a protected operation is reachable without required authentication or authentication is trivially bypassed.

### AUTH-002 Weak credential verification
Report plaintext password handling, insecure custom password hashing, missing verification, or misuse of privileged backend/service identities as interactive users.

### AUTH-003 Session weakness
Report predictable/reusable session IDs, fixation, unsafe regeneration, or insecure transport/storage.

For cookie sessions evaluate Secure, HttpOnly when appropriate, SameSite, scope, lifetime, rotation, and invalidation.

### AUTH-004 Signed token not cryptographically verified
For JWT/JWS/OAuth-style bearer tokens, report when claims are trusted without required cryptographic verification.

Check signature/MAC, allowed algorithm, correct key, issuer, audience, expiration/not-before, purpose/type, key rotation, and replay/revocation requirements.

Never apply this rule to NLP/LLM/parser tokens.

### AUTH-005 Missing token expiration
Report when an authentication/session/access token is intentionally non-expiring or excessively long-lived without compensating controls.

### AUTH-006 Logout/revocation failure
Report when security requirements demand invalidation but logout only changes client state and the credential remains usable.

### AUTH-007 Abuse protection missing
For exposed authentication, consider rate limiting, progressive delays, MFA/risk controls, monitoring, and lockout tradeoffs.

### AUTH-008 Sensitive action without fresh authentication
For high-risk actions, consider re-authentication or stronger transaction authorization.

## Common CWE mappings

- CWE-287 improper authentication
- CWE-306 missing authentication for critical function
- CWE-613 insufficient session expiration
- CWE-384 session fixation
