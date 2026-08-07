from collections.abc import Callable
from typing import Any

from runtime_tool_registry import ToolRegistry
from tool_contracts import TOOL_ARGUMENT_CONTRACTS
from tool_specs import TOOL_SPECS

from dataclasses import replace

from rag_runtime_tool import build_search_knowledge_runtime_tool
from rag_store import InMemoryRagStore


def build_default_tool_registry(
    *,
    tool_functions: dict[str, Callable[..., Any]],
    rag_store: InMemoryRagStore | None = None,
) -> ToolRegistry:
    runtime_tool_functions = dict(tool_functions)

    if rag_store is not None:
        runtime_tool_functions["search_knowledge"] = (
            build_search_knowledge_runtime_tool(store=rag_store)
        )

    registry = ToolRegistry()

    for tool_name, tool_function in runtime_tool_functions.items():
        registry.register(
            name=tool_name,
            function=tool_function,
            spec=TOOL_SPECS[tool_name],
            contract=TOOL_ARGUMENT_CONTRACTS[tool_name],
        )

    return registry

def build_runtime_tool_functions(
    *,
    tool_functions: dict[str, Callable[..., Any]],
    rag_store: InMemoryRagStore | None = None,
) -> dict[str, Callable[..., Any]]:
    runtime_tool_functions = dict(tool_functions)

    if rag_store is not None:
        runtime_tool_functions["search_knowledge"] = (
            build_search_knowledge_runtime_tool(store=rag_store)
        )

    return runtime_tool_functions

