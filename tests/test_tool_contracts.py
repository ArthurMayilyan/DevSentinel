from tool_contracts import validate_tool_arguments


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