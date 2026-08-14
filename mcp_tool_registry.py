from dataclasses import dataclass, field
from typing import Any

from mcp_tool_contract import (
    McpToolHandler,
    McpToolResult,
    McpToolSpec,
    validate_mcp_tool_spec,
)


@dataclass
class McpToolRegistry:
    specs: dict[str, McpToolSpec] = field(
        default_factory=dict,
    )
    handlers: dict[str, McpToolHandler] = field(
        default_factory=dict,
    )

    def register_spec(
        self,
        spec: McpToolSpec,
    ) -> None:
        validate_mcp_tool_spec(
            spec,
        )

        if spec.name in self.specs:
            raise ValueError(
                f"duplicate MCP tool spec: {spec.name}"
            )

        self.specs[spec.name] = spec

    def register_handler(
        self,
        *,
        name: str,
        handler: McpToolHandler,
    ) -> None:
        if name not in self.specs:
            raise ValueError(
                f"cannot register handler for unknown tool: {name}"
            )

        if not callable(
            handler,
        ):
            raise ValueError("handler must be callable.")

        self.handlers[name] = handler

    def list_specs(
        self,
    ) -> list[McpToolSpec]:
        return [
            self.specs[name]
            for name in sorted(
                self.specs,
            )
        ]

    def get_spec(
        self,
        name: str,
    ) -> McpToolSpec:
        if name not in self.specs:
            raise ValueError(
                f"unknown MCP tool: {name}"
            )

        return self.specs[
            name
        ]

    def execute(
        self,
        *,
        name: str,
        arguments: dict[str, Any],
    ) -> McpToolResult:
        if name not in self.specs:
            return McpToolResult(
                name=name,
                success=False,
                error=f"unknown MCP tool: {name}",
            )

        if name not in self.handlers:
            return McpToolResult(
                name=name,
                success=False,
                error=f"no handler registered for MCP tool: {name}",
            )

        try:
            result = self.handlers[name](
                arguments,
            )

            return McpToolResult(
                name=name,
                success=True,
                result=result,
            )
        except Exception as exc:
            return McpToolResult(
                name=name,
                success=False,
                error=str(
                    exc,
                ),
            )


def build_mcp_tool_registry(
    specs: list[McpToolSpec],
) -> McpToolRegistry:
    registry = McpToolRegistry()

    for spec in specs:
        registry.register_spec(
            spec,
        )

    return registry