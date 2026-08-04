from tool_contracts import validate_tool_arguments, format_tool_contract_for_prompt


def test_valid_read_file_arguments_pass():
    allowed, reason = validate_tool_arguments(
        tool_name="read_file",
        arguments={
            "path": "sample_project/auth.py",
        },
    )

    assert allowed is True
    assert reason == ""


def test_missing_required_argument_fails():
    allowed, reason = validate_tool_arguments(
        tool_name="read_file",
        arguments={},
    )

    assert allowed is False
    assert "missing" in reason.lower()
    assert "path" in reason


def test_unexpected_argument_fails():
    allowed, reason = validate_tool_arguments(
        tool_name="read_file",
        arguments={
            "path": "sample_project/auth.py",
            "mode": "unsafe",
        },
    )

    assert allowed is False
    assert "unexpected" in reason.lower()
    assert "mode" in reason


def test_write_report_requires_empty_arguments():
    allowed, reason = validate_tool_arguments(
        tool_name="write_report",
        arguments={
            "markdown": "# Fake report",
        },
    )

    assert allowed is False
    assert "unexpected" in reason.lower()
    assert "markdown" in reason


def test_unknown_tool_contract_fails():
    allowed, reason = validate_tool_arguments(
        tool_name="delete_project",
        arguments={
            "path": "./sample_project",
        },
    )

    assert allowed is False
    assert "no argument contract" in reason.lower()
    assert "delete_project" in reason

def test_path_must_be_non_empty_string():
    allowed, reason = validate_tool_arguments(
        tool_name="read_file",
        arguments={
            "path": "",
        },
    )

    assert allowed is False
    assert "path" in reason
    assert "non-empty string" in reason.lower()


def test_path_must_not_be_non_string():
    allowed, reason = validate_tool_arguments(
        tool_name="read_file",
        arguments={
            "path": 123,
        },
    )

    assert allowed is False
    assert "path" in reason
    assert "string" in reason.lower()


def test_add_finding_issue_must_be_non_empty_string():
    allowed, reason = validate_tool_arguments(
        tool_name="add_finding",
        arguments={
            "file": "sample_project/auth.py",
            "severity": "HIGH",
            "category": "SECURITY",
            "issue": "",
            "evidence": "login() grants access for hardcoded admin credentials.",
            "recommendation": "Remove hardcoded credentials.",
        },
    )

    assert allowed is False
    assert "issue" in reason
    assert "non-empty string" in reason.lower()

def test_add_finding_invalid_severity_fails():
    allowed, reason = validate_tool_arguments(
        tool_name="add_finding",
        arguments={
            "file": "sample_project/auth.py",
            "severity": "CRITICALITY_HIGH",
            "category": "SECURITY",
            "issue": "Authentication uses hardcoded administrator credentials.",
            "evidence": "login() grants access for hardcoded admin credentials.",
            "recommendation": "Remove hardcoded credentials.",
        },
    )

    assert allowed is False
    assert "severity" in reason.lower()
    assert "CRITICALITY_HIGH" in reason


def test_add_finding_invalid_category_fails():
    allowed, reason = validate_tool_arguments(
        tool_name="add_finding",
        arguments={
            "file": "sample_project/auth.py",
            "severity": "HIGH",
            "category": "Security",
            "issue": "Authentication uses hardcoded administrator credentials.",
            "evidence": "login() grants access for hardcoded admin credentials.",
            "recommendation": "Remove hardcoded credentials.",
        },
    )

    assert allowed is False
    assert "category" in reason.lower()
    assert "Security" in reason


def test_add_finding_valid_enum_values_pass():
    allowed, reason = validate_tool_arguments(
        tool_name="add_finding",
        arguments={
            "file": "sample_project/auth.py",
            "severity": "HIGH",
            "category": "SECURITY",
            "issue": "Authentication uses hardcoded administrator credentials.",
            "evidence": "login() grants access for hardcoded admin credentials.",
            "recommendation": "Remove hardcoded credentials.",
        },
    )

    assert allowed is True
    assert reason == ""



def test_format_tool_contract_for_prompt_includes_required_and_allowed_arguments():
    text = format_tool_contract_for_prompt("read_file")

    assert "Required arguments" in text
    assert "Allowed arguments" in text
    assert "path" in text


def test_format_tool_contract_for_prompt_includes_enum_values():
    text = format_tool_contract_for_prompt("add_finding")

    assert "Enum values" in text
    assert "severity" in text
    assert "LOW" in text
    assert "MEDIUM" in text
    assert "HIGH" in text
    assert "CRITICAL" in text

    assert "category" in text
    assert "SECURITY" in text
    assert "MAINTAINABILITY" in text
    assert "RELIABILITY" in text
    assert "PERFORMANCE" in text


def test_format_tool_contract_for_prompt_unknown_tool():
    text = format_tool_contract_for_prompt("delete_project")

    assert "No argument contract registered" in text
    assert "delete_project" in text    