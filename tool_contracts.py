from dataclasses import dataclass


@dataclass(frozen=True)
class ToolArgumentContract:
    required: set[str]
    allowed: set[str]
    non_empty_string_fields: set[str]


TOOL_ARGUMENT_CONTRACTS = {
    "list_files": ToolArgumentContract(
        required={"path"},
        allowed={"path"},
        non_empty_string_fields={"path"},
    ),
    "read_file": ToolArgumentContract(
        required={"path"},
        allowed={"path"},
        non_empty_string_fields={"path"},
    ),
    "search_in_files": ToolArgumentContract(
        required={"query", "path"},
        allowed={"query", "path"},
        non_empty_string_fields={"query", "path"},
    ),
    "add_finding": ToolArgumentContract(
        required={
            "file",
            "severity",
            "category",
            "issue",
            "evidence",
            "recommendation",
        },
        allowed={
            "file",
            "severity",
            "category",
            "issue",
            "evidence",
            "recommendation",
        },
        non_empty_string_fields={
            "file",
            "severity",
            "category",
            "issue",
            "evidence",
            "recommendation",
        },
    ),
    "write_report": ToolArgumentContract(
        required=set(),
        allowed=set(),
        non_empty_string_fields=set(),
    ),
}

def validate_tool_arguments(
    *,
    tool_name: str,
    arguments: dict,
) -> tuple[bool, str]:
    contract = TOOL_ARGUMENT_CONTRACTS.get(tool_name)

    if contract is None:
        return False, f"No argument contract registered for tool `{tool_name}`."

    argument_keys = set(arguments.keys())

    missing_arguments = sorted(contract.required - argument_keys)
    unexpected_arguments = sorted(argument_keys - contract.allowed)

    if missing_arguments:
        return (
            False,
            (
                f"Tool `{tool_name}` rejected: missing required arguments: "
                f"{missing_arguments}"
            ),
        )

    if unexpected_arguments:
        return (
            False,
            (
                f"Tool `{tool_name}` rejected: unexpected arguments: "
                f"{unexpected_arguments}"
            ),
        )

    for field_name in sorted(contract.non_empty_string_fields):
        value = arguments.get(field_name)

        if not isinstance(value, str):
            return (
                False,
                (
                    f"Tool `{tool_name}` rejected: argument `{field_name}` "
                    f"must be a non-empty string."
                ),
            )

        if not value.strip():
            return (
                False,
                (
                    f"Tool `{tool_name}` rejected: argument `{field_name}` "
                    f"must be a non-empty string."
                ),
            )

    return True, ""