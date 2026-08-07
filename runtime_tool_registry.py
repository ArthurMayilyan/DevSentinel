from dataclasses import dataclass
from typing import Callable, Any

from tool_contracts import (
    ToolArgumentContract,
    validate_tool_arguments,
    format_argument_contract_for_prompt,
)
from tool_specs import ToolSpec


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    function: Callable[..., Any]
    spec: ToolSpec
    contract: ToolArgumentContract


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(
        self,
        *,
        name: str,
        function: Callable[..., Any],
        spec: ToolSpec,
        contract: ToolArgumentContract,
    ) -> None:
        if not name:
            raise ValueError("Tool name must be non-empty.")

        if name in self._tools:
            raise ValueError(f"Tool `{name}` is already registered.")

        if spec.name != name:
            raise ValueError(
                f"Tool spec name mismatch: key is `{name}`, spec name is `{spec.name}`."
            )

        if not callable(function):
            raise ValueError(f"Tool `{name}` function must be callable.")

        self._tools[name] = RegisteredTool(
            name=name,
            function=function,
            spec=spec,
            contract=contract,
        )

    def names(self) -> list[str]:
        return sorted(self._tools.keys())

    def specs(self) -> list[Any]:
        return [
            self._tools[name].spec
            for name in sorted(self._tools)
        ]

    def registered_tools(self) -> list[RegisteredTool]:
        return [
            self._tools[name]
            for name in self.names()
        ]

    def has(self, name: str) -> bool:
        return name in self._tools

    def get(self, name: str) -> RegisteredTool:
        if name not in self._tools:
            raise KeyError(f"Tool `{name}` is not registered.")

        return self._tools[name]

    def function(self, name: str) -> Callable[..., Any]:
        return self.get(name).function

    def validate_arguments(
        self,
        *,
        tool_name: str,
        arguments: dict,
    ) -> tuple[bool, str]:
        if tool_name not in self._tools:
            return False, f"Tool `{tool_name}` is not registered."

        return validate_tool_arguments(
            tool_name=tool_name,
            arguments=arguments,
        )

    def execute(
        self,
        *,
        tool_name: str,
        arguments: dict,
    ) -> Any:
        allowed, reason = self.validate_arguments(
            tool_name=tool_name,
            arguments=arguments,
        )

        if not allowed:
            raise ValueError(reason)

        tool = self.get(tool_name)
        return tool.function(**arguments)

    def format_tools_for_prompt(self) -> str:
        descriptions = []

        for registered_tool in self.registered_tools():
            tool = registered_tool.spec
            argument_contract = format_argument_contract_for_prompt(
                registered_tool.contract
            )

            descriptions.append(
                f"""
    Tool: {tool.name}
    Description: {tool.description}
    Argument contract:
    {argument_contract}
    Returns: {tool.returns}
    When to use: {tool.when_to_use}
    When not to use: {tool.when_not_to_use}
    """
            )

        return "\n".join(descriptions)