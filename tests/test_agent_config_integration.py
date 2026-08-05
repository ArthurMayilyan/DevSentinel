import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from agent import Agent
from agent_config import AgentConfig
from trace import TraceRecorder


class DummyLLM:
    def complete(self, messages, state=None):
        raise RuntimeError("DummyLLM should not be called in this test.")


def test_agent_uses_default_config_from_max_steps_argument():
    agent = Agent(
        llm=DummyLLM(),
        trace_recorder=TraceRecorder(),
        max_steps=20,
    )

    assert agent.config.max_steps == 20
    assert agent.max_steps == 20


def test_agent_uses_injected_config():
    config = AgentConfig(max_steps=15)

    agent = Agent(
        llm=DummyLLM(),
        trace_recorder=TraceRecorder(),
        config=config,
    )

    assert agent.config is config
    assert agent.max_steps == 15

def test_agent_config_takes_precedence_over_max_steps_argument():
    config = AgentConfig(max_steps=5)

    agent = Agent(
        llm=DummyLLM(),
        trace_recorder=TraceRecorder(),
        max_steps=20,
        config=config,
    )

    assert agent.config is config
    assert agent.max_steps == 5