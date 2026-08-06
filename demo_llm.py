class DemoCodeReviewLLM:
    def complete(self, messages, state=None):
        if state is None:
            raise ValueError("DemoCodeReviewLLM requires agent state.")

        if not state.discovered_files:
            return {
                "type": "tool_call",
                "tool": "list_files",
                "arguments": {
                    "path": "./sample_project",
                },
            }

        python_files = sorted(
            file_path
            for file_path in state.discovered_files
            if file_path.endswith(".py")
        )

        for file_path in python_files:
            if file_path not in state.inspected_files:
                return {
                    "type": "tool_call",
                    "tool": "read_file",
                    "arguments": {
                        "path": file_path,
                    },
                }

        if not state.findings:
            return {
                "type": "tool_call",
                "tool": "add_finding",
                "arguments": {
                    "file": python_files[0],
                    "severity": "HIGH",
                    "category": "SECURITY",
                    "issue": "Hardcoded credential risk.",
                    "evidence": "A sensitive value appears directly in source code.",
                    "recommendation": "Move sensitive values to secure configuration.",
                },
            }

        if not state.report_written:
            return {
                "type": "tool_call",
                "tool": "write_report",
                "arguments": {},
            }

        return {
            "type": "final_answer",
            "answer": "Review complete. Report written to report.md.",
        }