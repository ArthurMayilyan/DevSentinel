
class ScriptedBadLLM:
    """
    Deterministic fake LLM for testing runtime guardrails.

    It returns predefined outputs one by one.
    This lets us simulate bad LLM behavior reliably.
    """

    def __init__(self, outputs: list[dict]):
        self.outputs = outputs
        self.call_count = 0

    def complete(self, messages: list[dict], state=None) -> dict:
        if self.call_count >= len(self.outputs):
            return {
                "type": "final_answer",
                "answer": "No more scripted outputs."
            }

        output = self.outputs[self.call_count]
        self.call_count += 1

        return output


def bad_final_answer_too_early_then_recovers() -> ScriptedBadLLM:
    return ScriptedBadLLM([
        # Bad behavior: tries to finish before inspecting files or writing report.
        {
            "type": "final_answer",
            "answer": "Review complete."
        },

        # Recovery path after runtime rejects the premature final answer.
        {
            "type": "tool_call",
            "tool": "list_files",
            "arguments": {
                "path": "./sample_project"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\app.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\auth.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\config.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Token verification accepts any non-empty token as valid.",
                "evidence": "verify_token(token) returns True whenever token is truthy.",
                "recommendation": "Validate token signature, expiry, issuer, audience, and revocation status."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Sensitive secrets and database credentials are hardcoded in source code.",
                "evidence": "config.py defines SECRET_KEY and DATABASE_URL with credentials.",
                "recommendation": "Move secrets to environment variables or a secrets manager."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\app.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "User profile endpoint exposes hardcoded administrative user data and debug state.",
                "evidence": "get_user_profile() returns fixed Admin profile and debug flag.",
                "recommendation": "Return authenticated user-specific profile data and avoid exposing debug state."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "Debug mode is enabled in configuration.",
                "evidence": "config.py sets DEBUG = True.",
                "recommendation": "Disable debug mode in production."
            }
        },
        {
            "type": "tool_call",
            "tool": "write_report",
            "arguments": {}
        },
        {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md."
        },
    ])

def bad_unknown_tool_then_recovers() -> ScriptedBadLLM:
    return ScriptedBadLLM([
        # Bad behavior: tries to call a tool that does not exist.
        {
            "type": "tool_call",
            "tool": "delete_project",
            "arguments": {
                "path": "./sample_project"
            }
        },

        # Recovery path after runtime rejects unknown tool.
        {
            "type": "tool_call",
            "tool": "list_files",
            "arguments": {
                "path": "./sample_project"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\app.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\auth.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\config.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Token verification accepts any non-empty token as valid.",
                "evidence": "verify_token(token) returns True whenever token is truthy.",
                "recommendation": "Validate token signature, expiry, issuer, audience, and revocation status."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Sensitive secrets and database credentials are hardcoded in source code.",
                "evidence": "config.py defines SECRET_KEY and DATABASE_URL with credentials.",
                "recommendation": "Move secrets to environment variables or a secrets manager."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\app.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "User profile endpoint exposes hardcoded administrative user data and debug state.",
                "evidence": "get_user_profile() returns fixed Admin profile and debug flag.",
                "recommendation": "Return authenticated user-specific profile data and avoid exposing debug state."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "Debug mode is enabled in configuration.",
                "evidence": "config.py sets DEBUG = True.",
                "recommendation": "Disable debug mode in production."
            }
        },
        {
            "type": "tool_call",
            "tool": "write_report",
            "arguments": {}
        },
        {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md."
        },
    ])

def bad_write_report_with_markdown_then_completes() -> ScriptedBadLLM:
    return ScriptedBadLLM([
        {
            "type": "tool_call",
            "tool": "list_files",
            "arguments": {
                "path": "./sample_project"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\app.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\auth.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\config.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Token verification accepts any non-empty token as valid.",
                "evidence": "verify_token(token) returns True whenever token is truthy.",
                "recommendation": "Validate token signature, expiry, issuer, audience, and revocation status."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Sensitive secrets and database credentials are hardcoded in source code.",
                "evidence": "config.py defines SECRET_KEY and DATABASE_URL with credentials.",
                "recommendation": "Move secrets to environment variables or a secrets manager."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\app.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "User profile endpoint exposes hardcoded administrative user data and debug state.",
                "evidence": "get_user_profile() returns fixed Admin profile and debug flag.",
                "recommendation": "Return authenticated user-specific profile data and avoid exposing debug state."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "Debug mode is enabled in configuration.",
                "evidence": "config.py sets DEBUG = True.",
                "recommendation": "Disable debug mode in production."
            }
        },

        # Bad behavior:
        # write_report should receive empty arguments only.
        {
            "type": "tool_call",
            "tool": "write_report",
            "arguments": {
                "markdown": "# Fake report from LLM\n\nThis content must be ignored by runtime."
            }
        },
        {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md."
        },
    ])


def bad_add_finding_before_read_then_recovers() -> ScriptedBadLLM:
    return ScriptedBadLLM([
        {
            "type": "tool_call",
            "tool": "list_files",
            "arguments": {
                "path": "./sample_project"
            }
        },

        # Bad behavior:
        # auth.py has not been read yet, but LLM tries to add a finding for it.
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },

        # Recovery path
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\app.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\auth.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\config.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Token verification accepts any non-empty token as valid.",
                "evidence": "verify_token(token) returns True whenever token is truthy.",
                "recommendation": "Validate token signature, expiry, issuer, audience, and revocation status."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Sensitive secrets and database credentials are hardcoded in source code.",
                "evidence": "config.py defines SECRET_KEY and DATABASE_URL with credentials.",
                "recommendation": "Move secrets to environment variables or a secrets manager."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\app.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "User profile endpoint exposes hardcoded administrative user data and debug state.",
                "evidence": "get_user_profile() returns fixed Admin profile and debug flag.",
                "recommendation": "Return authenticated user-specific profile data and avoid exposing debug state."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "Debug mode is enabled in configuration.",
                "evidence": "config.py sets DEBUG = True.",
                "recommendation": "Disable debug mode in production."
            }
        },
        {
            "type": "tool_call",
            "tool": "write_report",
            "arguments": {}
        },
        {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md."
        },
    ])

def bad_write_report_before_full_inspection_then_recovers() -> ScriptedBadLLM:
    return ScriptedBadLLM([
        {
            "type": "tool_call",
            "tool": "list_files",
            "arguments": {
                "path": "./sample_project"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\app.py"
            }
        },

        # Bad behavior:
        # auth.py and config.py are not inspected yet, and no findings exist.
        {
            "type": "tool_call",
            "tool": "write_report",
            "arguments": {}
        },

        # Recovery path
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\auth.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\config.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Token verification accepts any non-empty token as valid.",
                "evidence": "verify_token(token) returns True whenever token is truthy.",
                "recommendation": "Validate token signature, expiry, issuer, audience, and revocation status."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Sensitive secrets and database credentials are hardcoded in source code.",
                "evidence": "config.py defines SECRET_KEY and DATABASE_URL with credentials.",
                "recommendation": "Move secrets to environment variables or a secrets manager."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\app.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "User profile endpoint exposes hardcoded administrative user data and debug state.",
                "evidence": "get_user_profile() returns fixed Admin profile and debug flag.",
                "recommendation": "Return authenticated user-specific profile data and avoid exposing debug state."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "Debug mode is enabled in configuration.",
                "evidence": "config.py sets DEBUG = True.",
                "recommendation": "Disable debug mode in production."
            }
        },
        {
            "type": "tool_call",
            "tool": "write_report",
            "arguments": {}
        },
        {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md."
        },
    ])

def bad_add_finding_invalid_severity_then_recovers() -> ScriptedBadLLM:
    return ScriptedBadLLM([
        {
            "type": "tool_call",
            "tool": "list_files",
            "arguments": {
                "path": "./sample_project"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\app.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\auth.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\config.py"
            }
        },

        # Bad behavior:
        # severity is not allowed by IssueSeverity enum.
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "CRITICALITY_HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },

        # Recovery path
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Token verification accepts any non-empty token as valid.",
                "evidence": "verify_token(token) returns True whenever token is truthy.",
                "recommendation": "Validate token signature, expiry, issuer, audience, and revocation status."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Sensitive secrets and database credentials are hardcoded in source code.",
                "evidence": "config.py defines SECRET_KEY and DATABASE_URL with credentials.",
                "recommendation": "Move secrets to environment variables or a secrets manager."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\app.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "User profile endpoint exposes hardcoded administrative user data and debug state.",
                "evidence": "get_user_profile() returns fixed Admin profile and debug flag.",
                "recommendation": "Return authenticated user-specific profile data and avoid exposing debug state."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "Debug mode is enabled in configuration.",
                "evidence": "config.py sets DEBUG = True.",
                "recommendation": "Disable debug mode in production."
            }
        },
        {
            "type": "tool_call",
            "tool": "write_report",
            "arguments": {}
        },
        {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md."
        },
    ])

def bad_add_finding_invalid_category_then_recovers() -> ScriptedBadLLM:
    return ScriptedBadLLM([
        {
            "type": "tool_call",
            "tool": "list_files",
            "arguments": {
                "path": "./sample_project"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\app.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\auth.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\config.py"
            }
        },

        # Bad behavior:
        # category is not allowed by IssueCategory enum.
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "Security",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },

        # Recovery path
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Token verification accepts any non-empty token as valid.",
                "evidence": "verify_token(token) returns True whenever token is truthy.",
                "recommendation": "Validate token signature, expiry, issuer, audience, and revocation status."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Sensitive secrets and database credentials are hardcoded in source code.",
                "evidence": "config.py defines SECRET_KEY and DATABASE_URL with credentials.",
                "recommendation": "Move secrets to environment variables or a secrets manager."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\app.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "User profile endpoint exposes hardcoded administrative user data and debug state.",
                "evidence": "get_user_profile() returns fixed Admin profile and debug flag.",
                "recommendation": "Return authenticated user-specific profile data and avoid exposing debug state."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "Debug mode is enabled in configuration.",
                "evidence": "config.py sets DEBUG = True.",
                "recommendation": "Disable debug mode in production."
            }
        },
        {
            "type": "tool_call",
            "tool": "write_report",
            "arguments": {}
        },
        {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md."
        },
    ])    


def bad_tool_arguments_not_dict_then_recovers() -> ScriptedBadLLM:
    return ScriptedBadLLM([
        {
            "type": "tool_call",
            "tool": "list_files",
            "arguments": {
                "path": "./sample_project"
            }
        },

        # Bad behavior:
        # arguments must be a dict/object, not a string.
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": "sample_project\\auth.py"
        },

        # Recovery path
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\app.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\auth.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\config.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Token verification accepts any non-empty token as valid.",
                "evidence": "verify_token(token) returns True whenever token is truthy.",
                "recommendation": "Validate token signature, expiry, issuer, audience, and revocation status."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Sensitive secrets and database credentials are hardcoded in source code.",
                "evidence": "config.py defines SECRET_KEY and DATABASE_URL with credentials.",
                "recommendation": "Move secrets to environment variables or a secrets manager."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\app.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "User profile endpoint exposes hardcoded administrative user data and debug state.",
                "evidence": "get_user_profile() returns fixed Admin profile and debug flag.",
                "recommendation": "Return authenticated user-specific profile data and avoid exposing debug state."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "Debug mode is enabled in configuration.",
                "evidence": "config.py sets DEBUG = True.",
                "recommendation": "Disable debug mode in production."
            }
        },
        {
            "type": "tool_call",
            "tool": "write_report",
            "arguments": {}
        },
        {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md."
        },
    ])

def bad_read_file_missing_path_then_recovers() -> ScriptedBadLLM:
    return ScriptedBadLLM([
        {
            "type": "tool_call",
            "tool": "list_files",
            "arguments": {
                "path": "./sample_project"
            }
        },

        # Bad behavior:
        # read_file requires "path".
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {}
        },

        # Recovery path
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\app.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\auth.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\config.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Token verification accepts any non-empty token as valid.",
                "evidence": "verify_token(token) returns True whenever token is truthy.",
                "recommendation": "Validate token signature, expiry, issuer, audience, and revocation status."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Sensitive secrets and database credentials are hardcoded in source code.",
                "evidence": "config.py defines SECRET_KEY and DATABASE_URL with credentials.",
                "recommendation": "Move secrets to environment variables or a secrets manager."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\app.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "User profile endpoint exposes hardcoded administrative user data and debug state.",
                "evidence": "get_user_profile() returns fixed Admin profile and debug flag.",
                "recommendation": "Return authenticated user-specific profile data and avoid exposing debug state."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "Debug mode is enabled in configuration.",
                "evidence": "config.py sets DEBUG = True.",
                "recommendation": "Disable debug mode in production."
            }
        },
        {
            "type": "tool_call",
            "tool": "write_report",
            "arguments": {}
        },
        {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md."
        },
    ])

def bad_read_file_unexpected_argument_then_recovers() -> ScriptedBadLLM:
    return ScriptedBadLLM([
        {
            "type": "tool_call",
            "tool": "list_files",
            "arguments": {
                "path": "./sample_project"
            }
        },

        # Bad behavior:
        # read_file accepts only "path"; "mode" is unexpected.
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\auth.py",
                "mode": "unsafe"
            }
        },

        # Recovery path
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\app.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\auth.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\config.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Token verification accepts any non-empty token as valid.",
                "evidence": "verify_token(token) returns True whenever token is truthy.",
                "recommendation": "Validate token signature, expiry, issuer, audience, and revocation status."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Sensitive secrets and database credentials are hardcoded in source code.",
                "evidence": "config.py defines SECRET_KEY and DATABASE_URL with credentials.",
                "recommendation": "Move secrets to environment variables or a secrets manager."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\app.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "User profile endpoint exposes hardcoded administrative user data and debug state.",
                "evidence": "get_user_profile() returns fixed Admin profile and debug flag.",
                "recommendation": "Return authenticated user-specific profile data and avoid exposing debug state."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "Debug mode is enabled in configuration.",
                "evidence": "config.py sets DEBUG = True.",
                "recommendation": "Disable debug mode in production."
            }
        },
        {
            "type": "tool_call",
            "tool": "write_report",
            "arguments": {}
        },
        {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md."
        },
    ])

def bad_empty_final_answer_then_recovers() -> ScriptedBadLLM:
    return ScriptedBadLLM([
        {
            "type": "tool_call",
            "tool": "list_files",
            "arguments": {
                "path": "./sample_project"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\app.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\auth.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {
                "path": "sample_project\\config.py"
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Authentication uses hardcoded administrator credentials.",
                "evidence": "login() grants access when username == \"admin\" and password == \"admin\".",
                "recommendation": "Remove hardcoded credentials and use secure password hashing."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\auth.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Token verification accepts any non-empty token as valid.",
                "evidence": "verify_token(token) returns True whenever token is truthy.",
                "recommendation": "Validate token signature, expiry, issuer, audience, and revocation status."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "HIGH",
                "category": "SECURITY",
                "issue": "Sensitive secrets and database credentials are hardcoded in source code.",
                "evidence": "config.py defines SECRET_KEY and DATABASE_URL with credentials.",
                "recommendation": "Move secrets to environment variables or a secrets manager."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\app.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "User profile endpoint exposes hardcoded administrative user data and debug state.",
                "evidence": "get_user_profile() returns fixed Admin profile and debug flag.",
                "recommendation": "Return authenticated user-specific profile data and avoid exposing debug state."
            }
        },
        {
            "type": "tool_call",
            "tool": "add_finding",
            "arguments": {
                "file": "sample_project\\config.py",
                "severity": "MEDIUM",
                "category": "SECURITY",
                "issue": "Debug mode is enabled in configuration.",
                "evidence": "config.py sets DEBUG = True.",
                "recommendation": "Disable debug mode in production."
            }
        },
        {
            "type": "tool_call",
            "tool": "write_report",
            "arguments": {}
        },

        # Bad behavior:
        # final_answer exists, but answer is empty.
        {
            "type": "final_answer",
            "answer": ""
        },

        # Recovery path
        {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md."
        },
    ])