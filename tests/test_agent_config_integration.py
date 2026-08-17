import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from agent import Agent
from agent_config import AgentConfig
from trace import TraceRecorder
from rag_store import InMemoryRagStore


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

def test_agent_accepts_run_metadata():
    run_metadata = {
        "llm": "demo",
        "preset": "code-review",
        "path": "./sample_project",
    }

    agent = Agent(
        llm=DummyLLM(),
        trace_recorder=TraceRecorder(),
        run_metadata=run_metadata,
    )

    assert agent.run_metadata is run_metadata


def test_agent_rejects_non_dict_run_metadata():
    with pytest.raises(ValueError):
        Agent(
            llm=DummyLLM(),
            trace_recorder=TraceRecorder(),
            run_metadata="not metadata",
        )    

def test_agent_registers_search_knowledge_when_rag_store_is_provided():
    rag_store = InMemoryRagStore()
    rag_store.add_document(
        source="security.md",
        text="Tokens must be signed and must expire.",
    )

    agent = Agent(
        llm=DummyLLM(),
        trace_recorder=TraceRecorder(),
        rag_store=rag_store,
    )

    assert "search_knowledge" in agent.tool_registry.names()

def test_agent_does_not_register_search_knowledge_without_rag_store():
    agent = Agent(
        llm=DummyLLM(),
        trace_recorder=TraceRecorder(),
    )

    assert "search_knowledge" not in agent.tool_registry.names()


from agent import Agent
from agent_config import AgentConfig
from app_settings import get_app_settings
from trace import TraceRecorder


class MinimalFakeLLM:
    def complete(
        self,
        messages,
        state=None,
    ):
        return {
            "type": "final_answer",
            "answer": "done",
        }


def test_agent_uses_configured_max_steps_when_not_explicitly_provided():
    settings = get_app_settings()

    agent = Agent(
        llm=MinimalFakeLLM(),
        trace_recorder=TraceRecorder(),
    )

    assert agent.max_steps == (
        settings.agent.max_steps
    )


def test_agent_explicit_max_steps_overrides_configured_default():
    agent = Agent(
        llm=MinimalFakeLLM(),
        trace_recorder=TraceRecorder(),
        max_steps=17,
    )

    assert agent.max_steps == 17                