In the file: sample_project\auth.py
Found evidence: login() authenticates only when username == "admin" and password == "admin".
Severity: HIGH

In the file: sample_project\auth.py
Found evidence: verify_token(token) returns True whenever token is truthy and performs no signature, expiry, issuer, audience, or revocation validation.
Severity: HIGH

In the file: sample_project\config.py
Found evidence: config.py defines SECRET_KEY = "super-secret-hardcoded-key" and DATABASE_URL = "postgresql://admin:admin@localhost:5432/app".
Severity: HIGH

In the file: sample_project\config.py
Found evidence: config.py sets DEBUG = True, and app.py returns this value in the get_user_profile() response.
Severity: MEDIUM

In the file: sample_project\app.py
Found evidence: get_user_profile() returns name "Admin", email "admin@example.com", and "debug": DEBUG for any request with a token that verify_token() accepts.
Severity: MEDIUM

