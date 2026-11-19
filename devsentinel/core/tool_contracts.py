from dataclasses import dataclass


@dataclass(frozen=True)
class ToolArgumentContract:
    required: set[str]
    allowed: set[str]
    non_empty_string_fields: set[str]
    enum_fields: dict[str, set[str]]


TOOL_ARGUMENT_CONTRACTS = {
    "list_files": ToolArgumentContract(
        required={"path"},
        allowed={"path"},
        non_empty_string_fields={"path"},
        enum_fields={},
    ),
    "read_file": ToolArgumentContract(
        required={"path"},
        allowed={"path"},
        non_empty_string_fields={"path"},
        enum_fields={},
    ),
    "search_in_files": ToolArgumentContract(
        required={"query", "path"},
        allowed={"query", "path"},
        non_empty_string_fields={"query", "path"},
        enum_fields={},
    ),
    "search_knowledge": ToolArgumentContract(
        allowed={"query"},
        required={"query"},
        non_empty_string_fields={"query"},
        enum_fields={},
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
        enum_fields={
            "severity": {"LOW", "MEDIUM", "HIGH", "CRITICAL"},
            "category": {
                "SECURITY",
                "MAINTAINABILITY",
                "RELIABILITY",
                "PERFORMANCE",
            },
        },
    ),
    "write_report": ToolArgumentContract(
        required=set(),
        allowed=set(),
        non_empty_string_fields=set(),
        enum_fields={},
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

    for field_name, allowed_values in contract.enum_fields.items():
        value = arguments.get(field_name)

        if value not in allowed_values:
            return (
                False,
                (
                    f"Tool `{tool_name}` rejected: argument `{field_name}` "
                    f"has invalid value `{value}`. "
                    f"Allowed values: {sorted(allowed_values)}"
                ),
            )        

    return True, ""

def format_tool_contract_for_prompt(tool_name: str) -> str:
    contract = TOOL_ARGUMENT_CONTRACTS.get(tool_name)

    if contract is None:
        return f"No argument contract registered for tool `{tool_name}`."

    return format_argument_contract_for_prompt(contract)

def format_argument_contract_for_prompt(contract: ToolArgumentContract) -> str:
    lines = [
        f"Required arguments: {sorted(contract.required)}",
        f"Allowed arguments: {sorted(contract.allowed)}",
        f"Non-empty string fields: {sorted(contract.non_empty_string_fields)}",
    ]

    if contract.enum_fields:
        lines.append("Enum values:")

        for field_name, allowed_values in sorted(contract.enum_fields.items()):
            lines.append(f"- {field_name}: {sorted(allowed_values)}")
    else:
        lines.append("Enum values: none")

    return "\n".join(lines)