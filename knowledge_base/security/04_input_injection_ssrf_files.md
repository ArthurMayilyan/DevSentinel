# Input Validation, Injection, SSRF, and File/Path Safety

## Objective

Untrusted input must not become executable control syntax, escape intended resource boundaries, or make servers contact unintended destinations.

## Rules

### INJ-001 SQL/NoSQL/query injection
Report attacker-controlled data changing query structure through concatenation/interpolation or unsafe dynamic queries.

Prefer parameterized queries/bind variables. Use allowlists for structural identifiers when binding cannot apply.

### INJ-002 OS command injection
Report untrusted data reaching a shell/command interpreter as command text.

Prefer avoiding shell execution and using executable/argument APIs plus strict allowlists.

### INJ-003 Dynamic code/template/expression injection
Report unsafe eval/template/expression execution when external input controls executable content.

### INJ-004 Path traversal / arbitrary file access
Report when untrusted path components can escape the intended root or select unintended files.

Prefer canonical resolution plus containment checks, rejecting unsafe absolute/traversal paths, or mapping opaque IDs to server-owned paths.

### INJ-005 Unsafe file upload
Review file type/content policy, generated storage names, executable storage locations, size/resource limits, authorization, and malware/content scanning where required.

### SSRF-001 Server-side request forgery
HIGH when attacker-controlled destinations can make the server reach internal, metadata, loopback, admin, or restricted services.

Controls can include destination allowlists, scheme/host/port validation, IP/network restrictions, redirect controls, network egress policy, and cloud-metadata protection.

### VAL-001 Missing syntactic/semantic validation
Report malformed/out-of-policy data when it materially affects a security boundary or dangerous downstream operation.

Third-party/service input is not automatically trusted.

## False positives

Do not report:
- parameterized SQL merely because SQL text exists;
- fixed subprocess execution with controlled args;
- paths proven to remain inside an allowed root;
- immutable allowlisted external endpoints.

## Common CWE mappings

- CWE-89 SQL injection
- CWE-78 OS command injection
- CWE-79 XSS
- CWE-22 path traversal
- CWE-918 SSRF
