CODE_REVIEW_JSON_EXAMPLES = [
    '''{
  "type": "tool_call",
  "tool": "list_files",
  "arguments": {
    "path": "./sample_project"
  }
}''',
    '''{
  "type": "tool_call",
  "tool": "read_file",
  "arguments": {
    "path": "sample_project/auth.py"
  }
}''',
    '''{
  "type": "tool_call",
  "tool": "add_finding",
  "arguments": {
    "file": "sample_project/auth.py",
    "severity": "HIGH",
    "category": "SECURITY",
    "issue": "Authentication uses hardcoded administrator credentials.",
    "evidence": "login() grants access when username == \\"admin\\" and password == \\"admin\\".",
    "recommendation": "Remove hardcoded credentials and use secure password hashing."
  }
}''',
    '''{
  "type": "tool_call",
  "tool": "write_report",
  "arguments": {}
}''',
    '''{
  "type": "final_answer",
  "answer": "Review complete. Report written to report.md."
}''',
]