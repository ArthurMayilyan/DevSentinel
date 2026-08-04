import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from agent import Agent
from tool_specs import TOOL_SPECS
from tool_contracts import TOOL_ARGUMENT_CONTRACTS
from trace import TraceRecorder
from runtime_tool_registry import ToolRegistry

class DummyLLM:
    def complete(self, messages, state=None):
        raise RuntimeError("DummyLLM should not be called in this test.")

def dummy_read_file(path: str) -> str:
    return f"read: {path}"

def make_agent() -> Agent:
    return Agent(
        llm=DummyLLM(),
        trace_recorder=TraceRecorder(),
        max_steps=1,
    )


def test_every_tool_spec_has_argument_contract():
    assert set(TOOL_SPECS.keys()) == set(TOOL_ARGUMENT_CONTRACTS.keys())


def test_every_tool_spec_key_matches_tool_name():
    for tool_key, tool_spec in TOOL_SPECS.items():
        assert tool_spec.name == tool_key


def test_agent_registered_tools_match_tool_specs():
    agent = make_agent()

    assert set(agent._tools.keys()) == set(TOOL_SPECS.keys())


def test_all_agent_registered_tools_are_callable():
    agent = make_agent()

    for tool_name, tool_function in agent._tools.items():
        assert callable(tool_function), f"Tool `{tool_name}` is not callable."

def test_agent_tool_registry_matches_agent_tools():
    agent = make_agent()

    assert set(agent.tool_registry.names()) == set(agent._tools.keys())


def test_agent_tool_registry_matches_tool_specs():
    agent = make_agent()

    assert set(agent.tool_registry.names()) == set(TOOL_SPECS.keys())


def test_agent_tool_registry_can_validate_read_file_arguments():
    agent = make_agent()

    allowed, reason = agent.tool_registry.validate_arguments(
        tool_name="read_file",
        arguments={
            "path": "sample_project/auth.py",
        },
    )

    assert allowed is True
    assert reason == ""        

def test_agent_can_use_injected_tool_registry():
    registry = ToolRegistry()

    registry.register(
        name="read_file",
        function=dummy_read_file,
        spec=TOOL_SPECS["read_file"],
        contract=TOOL_ARGUMENT_CONTRACTS["read_file"],
    )

    agent = Agent(
        llm=DummyLLM(),
        trace_recorder=TraceRecorder(),
        max_steps=1,
        tool_registry=registry,
    )

    assert agent.tool_registry is registry
    assert agent.tool_registry.names() == ["read_file"]


def test_agent_prompt_uses_injected_tool_registry():
    registry = ToolRegistry()

    registry.register(
        name="read_file",
        function=dummy_read_file,
        spec=TOOL_SPECS["read_file"],
        contract=TOOL_ARGUMENT_CONTRACTS["read_file"],
    )

    agent = Agent(
        llm=DummyLLM(),
        trace_recorder=TraceRecorder(),
        max_steps=1,
        tool_registry=registry,
    )

    text = agent.build_tools_description()

    assert "Tool: read_file" in text
    assert "Tool: write_report" not in text
    assert "Tool: add_finding" not in text

