In the file: sample_project\config.py
Found evidence: SECRET_KEY = "super-secret-hardcoded-key"
Severity: HIGH

In the file: sample_project\config.py
Found evidence: DATABASE_URL = "postgresql://admin:admin@localhost:5432/app"
Severity: HIGH

In the file: sample_project\auth.py
Found evidence: if username == "admin" and password == "admin":
Severity: HIGH

In the file: sample_project\auth.py
Found evidence: The token validation logic accepts any non-empty token.
Severity: HIGH

In the file: sample_project\app.py
Found evidence: "debug": DEBUG in the user profile response
Severity: MEDIUM

