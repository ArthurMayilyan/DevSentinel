from collections.abc import Callable
from typing import Any

from runtime_tool_registry import ToolRegistry
from tool_contracts import TOOL_ARGUMENT_CONTRACTS
from tool_specs import TOOL_SPECS


def build_default_tool_registry(
    *,
    tool_functions: dict[str, Callable[..., Any]],
) -> ToolRegistry:
    registry = ToolRegistry()

    for tool_name, tool_function in tool_functions.items():
        registry.register(
            name=tool_name,
            function=tool_function,
            spec=TOOL_SPECS[tool_name],
            contract=TOOL_ARGUMENT_CONTRACTS[tool_name],
        )

    return registry