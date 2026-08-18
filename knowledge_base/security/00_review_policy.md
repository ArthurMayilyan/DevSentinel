# Security Review Policy

## Evidence standard

A valid finding should normally identify:
- asset at risk;
- untrusted/sensitive source;
- relevant data/control path;
- dangerous sink or security decision;
- missing protection;
- production or meaningful environment reachability.

Do not create a finding from a keyword alone.

## Mandatory false-positive checks

Before reporting, determine whether the code is:
- a unit/integration test, fixture, mock, sample, benchmark, tutorial, or intentionally vulnerable target;
- a security detector/rule containing strings such as SECRET_KEY, password, admin, DEBUG, jwt, or token;
- documentation or prompt text;
- fake data or fake model output;
- generated metadata;
- code whose security control is enforced by middleware/gateway/caller.

These contexts can still be risky, but the report must explain the real execution path.

## Token terminology

Do not report authentication-token weaknesses for LLM tokens, tokenizer output, parser tokens, pagination tokens, or other non-security tokens.

Authentication/session token findings require identity/security semantics such as bearer, access, refresh, session, auth, JWT/JWS/JWE, OAuth/OIDC, API key, principal, issuer, audience, or claims.

## Secret rule

Strong evidence:
- usable provider credential/private key;
- credential used in authentication/database connection;
- key used for signing/encryption;
- production endpoint plus credential;
- explicit API key/password/client secret in executable config.

Weak evidence that must not stand alone:
- variable named SECRET_KEY;
- placeholder values;
- detector regex;
- documentation;
- fake LLM response.

If a real secret entered source control, remediation includes revocation/rotation, not only deleting the line.

## Debug rule

Report debug mode only when runtime/deployment configuration enables it in a meaningful environment or when external responses expose sensitive diagnostics.

Do not report logger debug calls, rule definitions, or ordinary uses of the word debug.

## Authentication/authorization rule

Do not infer bypass merely because a function accepts a token. Identify what authenticates the caller, how authenticity is verified, what expiration/revocation applies, and what authorization decision follows.

## Injection rule

Require a data-flow relationship between untrusted input and an interpreter/dangerous operation. Do not report safe parameterized APIs merely because query text exists.

## Reporting fields

Prefer:
- severity;
- category;
- stable finding type;
- file/location;
- concise issue;
- concrete evidence;
- impact;
- recommendation;
- confidence when supported;
- relevant standard/CWE mapping where useful.
