from agent_state import AgentState


def evaluate_run(state: AgentState, eval_case: dict) -> dict:
    results = {
        "passed": True,
        "failures": []
    }

    for file in eval_case["must_inspect_files"]:
        if file not in state.inspected_files:
            results["passed"] = False
            results["failures"].append(f"Required file not inspected: {file}")

    for tool in eval_case["must_use_tools"]:
        if tool not in state.tools_used:
            results["passed"] = False
            results["failures"].append(f"Required tool not used: {tool}")

    for expected in eval_case["expected_findings"]:
        matched = False

        for finding in state.findings:
            if (
                finding["file"] == expected["file"]
                and expected["issue_contains"].lower() in finding["issue"].lower()
                and finding["severity"] == expected["severity"]
            ):
                matched = True
                break

        if not matched:
            results["passed"] = False
            results["failures"].append(f"Expected finding not found: {expected}")

    return results