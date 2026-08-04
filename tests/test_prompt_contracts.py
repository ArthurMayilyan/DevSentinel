import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from agent import Agent
from trace import TraceRecorder


class DummyLLM:
    def complete(self, messages, state=None):
        raise RuntimeError("DummyLLM should not be called in this test.")


def make_agent() -> Agent:
    return Agent(
        llm=DummyLLM(),
        trace_recorder=TraceRecorder(),
        max_steps=1,
    )


def test_tools_description_includes_argument_contract_section():
    agent = make_agent()

    text = agent.build_tools_description()

    assert "Argument contract:" in text
    assert "Required arguments" in text
    assert "Allowed arguments" in text


def test_add_finding_prompt_contract_includes_enum_values():
    agent = make_agent()

    text = agent.build_tools_description()

    assert "Tool: add_finding" in text
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


def test_write_report_prompt_contract_requires_empty_arguments():
    agent = make_agent()

    text = agent.build_tools_description()

    assert "Tool: write_report" in text
    assert "Required arguments: []" in text
    assert "Allowed arguments: []" in text