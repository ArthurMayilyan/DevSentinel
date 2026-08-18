# Authorization and Access Control

## Objective

Every protected object and operation must enforce server-side authorization according to principal, tenant, object, action, and business policy.

## Rules

### AUTHZ-001 Missing object-level authorization
HIGH when a user-controlled identifier selects a resource without verifying caller access.

### AUTHZ-002 Missing function-level authorization
HIGH when privileged/admin functions rely only on hidden UI, route naming, client flags, or possession of an identifier.

### AUTHZ-003 Mass assignment / property authorization
Report when request binding allows clients to set protected fields such as role, owner/tenant, price, approval state, internal flags, or permissions.

Prefer explicit allowlisted input schemas.

### AUTHZ-004 Tenant isolation failure
CRITICAL/HIGH when one tenant can access another tenant's data because tenant scope is missing or attacker-controlled.

### AUTHZ-005 Privilege escalation
Report when users can grant themselves/others privileges or security decisions trust mutable/unverified client claims.

### AUTHZ-006 Alternate-path bypass
Report when another route, method, API version, direct storage path, or internal endpoint bypasses the intended policy.

### AUTHZ-007 Fail-open policy
Report authorization that grants on exception, unknown role, missing policy data, or unsupported state.

## Expectations

- deny by default;
- least privilege;
- server-side enforcement;
- authentication separate from authorization;
- tenant/business context in policy;
- negative authorization tests.

## False positives

A helper lacking an authorization check is not necessarily vulnerable if authorization is reliably enforced by middleware/decorator/gateway/caller. Verify the real boundary.

## Common CWE mappings

- CWE-862 missing authorization
- CWE-863 incorrect authorization
- CWE-639 authorization bypass through user-controlled key
