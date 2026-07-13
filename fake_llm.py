from tool_specs import IssueSeverity, IssueCategory

class FakeLLM:
    def __init__(self):
        self.step = 0

    def complete(self, messages: list[dict], state) -> dict:
        self.step += 1

        if self.step == 1:
            return {
                "type": "tool_call",
                "tool": "list_files",
                "arguments": {
                    "path": "./sample_project"
                }
            }

        if self.step == 2:
            return {
                "type": "tool_call",
                "tool": "read_file",
                "arguments": {
                    "path": "sample_project\\config.py"
                }
            }

        if self.step == 3:
            return {
                "type": "tool_call",
                "tool": "add_finding",
                "arguments": {
                    "file": "sample_project\\config.py",
                    "severity": IssueSeverity.HIGH,
                    "category": IssueCategory.SECURITY,
                    "issue": "Hardcoded SECRET_KEY found",
                    "evidence": "SECRET_KEY = \"super-secret-hardcoded-key\"",
                    "recommendation": "Move SECRET_KEY to environment variables or a secure vault.",
                }
            }

        if self.step == 4:
            return {
                "type": "tool_call",
                "tool": "add_finding",
                "arguments": {
                    "file": "sample_project\\config.py",
                    "severity": IssueSeverity.HIGH,
                    "category": IssueCategory.SECURITY,
                    "issue": "Hardcoded DATABASE_URL found",
                    "evidence": "DATABASE_URL = \"postgresql://admin:admin@localhost:5432/app\"",
                    "recommendation": "Move DATABASE_URL to environment variables or a secure vault.",
                }
            }

        if self.step == 5:
            return {
                "type": "tool_call",
                "tool": "read_file",
                "arguments": {
                    "path": "sample_project\\auth.py"
                }
            }
        
        if self.step == 6:
            return {
                "type": "tool_call",
                "tool": "add_finding",
                "arguments": {
                    "file": "sample_project\\auth.py",
                    "severity": IssueSeverity.HIGH,
                    "category": IssueCategory.SECURITY,
                    "issue": "Hardcoded admin credentials",
                    "evidence": "if username == \"admin\" and password == \"admin\":",
                    "recommendation": "Move admin credentials to environment variables or a secure vault.",
                }
            }

        if self.step == 7:
            return {
                "type": "tool_call",
                "tool": "add_finding",
                "arguments": {
                    "file": "sample_project\\auth.py",
                    "severity": IssueSeverity.HIGH,
                    "category": IssueCategory.SECURITY,
                    "issue": "Weak token validation",
                    "evidence": "The token validation logic accepts any non-empty token.",
                    "recommendation": "Implement proper token validation.",
                }
            }

        if self.step == 8:
            return {
                "type": "tool_call",
                "tool": "read_file",
                "arguments": {
                    "path": "sample_project\\app.py"
                }
            }
        
        if self.step == 9:
            return {
                "type": "tool_call",
                "tool": "add_finding",
                "arguments": {
                    "file": "sample_project\\app.py",
                    "severity": IssueSeverity.MEDIUM,
                    "category": IssueCategory.SECURITY,
                    "issue": "DEBUG statement found in code",
                    "evidence": "\"debug\": DEBUG in the user profile response",
                    "recommendation": "Remove DEBUG statements before deploying to production.",
                }
            }

        if self.step == 10:
            return {
                "type": "tool_call",
                "tool": "write_report",
                "arguments": {
                    "markdown": (
                        "# Review Report\n\n"
                        "## Security Issues\n\n"
                        "1. `config.py` contains hardcoded secrets.\n"
                        "2. `auth.py` accepts hardcoded admin credentials.\n"
                        "3. `app.py` contains DEBUG statements.\n\n"
                        "## Limitations\n\n"
                        "This review was based only on static file inspection.\n"
                    )
                }
            }

        return {
            "type": "final_answer",
            "answer": (
                "Review completed. I inspected config.py, app.py and auth.py. "
                "I found hardcoded secrets, hardcoded credentials, and weak token validation. "
                "The report was saved to report.md."
            )
        }
