from prompt_builder import PromptBuilder


def test_prompt_builder_includes_tools_description():
    builder = PromptBuilder()

    prompt = builder.build_system_prompt(
        tools_description="Tool: read_file"
    )

    assert "Tool: read_file" in prompt


def test_prompt_builder_includes_json_protocol():
    builder = PromptBuilder()

    prompt = builder.build_system_prompt(
        tools_description="Tool: read_file"
    )

    assert '"type": "tool_call"' in prompt
    assert '"type": "final_answer"' in prompt


def test_prompt_builder_includes_guardrail_rules():
    builder = PromptBuilder()

    prompt = builder.build_system_prompt(
        tools_description="Tool: read_file"
    )

    assert "Do not invent findings before reading files" in prompt
    assert "Do not provide final_answer before the report is written" in prompt
    assert "final_answer.answer must be a non-empty string" in prompt

def test_prompt_builder_uses_custom_agent_role():
    builder = PromptBuilder(
        agent_role="a documentation review agent",
    )

    prompt = builder.build_system_prompt(
        tools_description="Tool: read_file"
    )

    assert "You are a documentation review agent." in prompt

def test_prompt_builder_uses_custom_task_description():
    builder = PromptBuilder(
        task_description="review documentation for clarity and completeness",
    )

    prompt = builder.build_system_prompt(
        tools_description="Tool: read_file"
    )

    assert (
        "Your task is to review documentation for clarity and completeness."
        in prompt
    )    

def test_prompt_builder_uses_default_rules():
    builder = PromptBuilder()

    prompt = builder.build_system_prompt(
        tools_description="Tool: read_file"
    )

    assert "- Use only available tools." in prompt
    assert "- Tool arguments must follow the tool argument contract." in prompt


def test_prompt_builder_uses_custom_rules():
    builder = PromptBuilder(
        rules=[
            "Read documentation before writing findings.",
            "Do not modify files.",
        ],
    )

    prompt = builder.build_system_prompt(
        tools_description="Tool: read_file"
    )

    assert "- Read documentation before writing findings." in prompt
    assert "- Do not modify files." in prompt
    assert "- Use only available tools." not in prompt

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from agent import Agent
from prompt_builder import PromptBuilder
from trace import TraceRecorder


class DummyLLM:
    def complete(self, messages, state=None):
        raise RuntimeError("DummyLLM should not be called in this test.")


def test_agent_uses_injected_prompt_builder():
    prompt_builder = PromptBuilder(
        agent_role="a documentation review agent",
        task_description="review documentation for clarity",
        rules=[
            "Use only read-only tools.",
        ],
    )

    agent = Agent(
        llm=DummyLLM(),
        trace_recorder=TraceRecorder(),
        max_steps=1,
        prompt_builder=prompt_builder,
    )

    assert agent.prompt_builder is prompt_builder

    prompt = agent.build_system_prompt()

    assert "You are a documentation review agent." in prompt
    assert "Your task is to review documentation for clarity." in prompt
    assert "- Use only read-only tools." in prompt

def test_prompt_builder_omits_examples_section_by_default():
    builder = PromptBuilder()

    prompt = builder.build_system_prompt(
        tools_description="Tool: read_file"
    )

    assert "Examples:" not in prompt


def test_prompt_builder_includes_custom_examples():
    builder = PromptBuilder(
        examples=[
            '{\n  "type": "tool_call",\n  "tool": "list_files",\n  "arguments": {\n    "path": "./sample_project"\n  }\n}',
            '{\n  "type": "final_answer",\n  "answer": "Review complete. Report written to report.md."\n}',
        ],
    )

    prompt = builder.build_system_prompt(
        tools_description="Tool: read_file"
    )

    assert "Examples:" in prompt
    assert '"tool": "list_files"' in prompt
    assert '"type": "final_answer"' in prompt
    assert "Review complete. Report written to report.md." in prompt


        