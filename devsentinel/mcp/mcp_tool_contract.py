from dataclasses import asdict, dataclass
from typing import Any, Callable


JsonDict = dict[str, Any]
McpToolHandler = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class McpToolSpec:
    name: str
    description: str
    input_schema: JsonDict
    output_schema: JsonDict


@dataclass(frozen=True)
class McpToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class McpToolResult:
    name: str
    success: bool
    result: Any = None
    error: str = ""


def validate_json_schema_object(
    *,
    value: dict[str, Any],
    field_name: str,
) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dictionary.")

    if value.get("type") != "object":
        raise ValueError(f"{field_name} must be an object schema.")

    properties = value.get("properties")

    if properties is not None and not isinstance(properties, dict):
        raise ValueError(f"{field_name}.properties must be a dictionary.")


def validate_mcp_tool_spec(
    spec: McpToolSpec,
) -> None:
    if not isinstance(spec.name, str) or not spec.name.strip():
        raise ValueError("tool name must be a non-empty string.")

    if not isinstance(spec.description, str) or not spec.description.strip():
        raise ValueError("tool description must be a non-empty string.")

    validate_json_schema_object(
        value=spec.input_schema,
        field_name="input_schema",
    )

    validate_json_schema_object(
        value=spec.output_schema,
        field_name="output_schema",
    )


def mcp_tool_spec_to_dict(
    spec: McpToolSpec,
) -> dict[str, Any]:
    validate_mcp_tool_spec(
        spec,
    )

    return asdict(
        spec,
    )


def mcp_tool_spec_to_mcp_tool(
    spec: McpToolSpec,
) -> dict[str, Any]:
    validate_mcp_tool_spec(
        spec,
    )

    return {
        "name": spec.name,
        "description": spec.description,
        "inputSchema": spec.input_schema,
    }


def mcp_tool_result_to_dict(
    result: McpToolResult,
) -> dict[str, Any]:
    return asdict(
        result,
    )

