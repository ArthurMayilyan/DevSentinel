import json
import os
from pathlib import Path
from uuid import uuid4

import pytest

from devsentinel.core.agent import Agent
from devsentinel.core.agent_config import AgentConfig
from devsentinel.core.agent_stop_reasons import (
    STOP_CODE_REJECTED_TOOL_CALLS,
)
from devsentinel.core.tool_path_utils import (
    PATH_REJECTION_OUTSIDE_PROJECT_ROOT,
    PATH_REJECTION_PROJECT_ROOT_NOT_CONFIGURED,
    build_project_scope,
)
from devsentinel.core.trace import TraceRecorder
from devsentinel.llm.bad_llm import ScriptedBadLLM


class RecordingScriptedLLM(ScriptedBadLLM):
    """Scripted LLM that keeps every message it was shown."""

    def __init__(self, outputs: list[object]):
        super().__init__(outputs)
        self.seen_messages: list[str] = []

    def complete(self, messages: list[dict], state=None) -> dict:
        self.seen_messages.extend(
            str(message.get("content", ""))
            for message in messages
        )

        return super().complete(messages, state)


class AlwaysEscapeLLM:
    def complete(self, messages, state=None):
        return {
            "type": "tool_call",
            "tool": "read_file",
            "arguments": {"path": "../canary.txt"},
        }


@pytest.fixture
def sandbox(tmp_path):
    token = f"CANARY-{uuid4().hex}"
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text(
        'SECRET_KEY = "hardcoded"\n',
        encoding="utf-8",
    )

    canary = tmp_path / "canary.txt"
    canary.write_text(token, encoding="utf-8")

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "leak.py").write_text(f"TOKEN = '{token}'\n", encoding="utf-8")

    return {
        "token": token,
        "project": project,
        "canary": canary,
        "outside_dir": outside_dir,
        "scope": build_project_scope(root=project),
        "report_path": str(tmp_path / "report.md"),
    }


def tool_call(tool: str, **arguments) -> dict:
    return {
        "type": "tool_call",
        "tool": tool,
        "arguments": arguments,
    }


def escape_then_recover_script(*, escape_paths: list[str]) -> list[dict]:
    return [
        tool_call("list_files", path="."),
        *[tool_call("read_file", path=path) for path in escape_paths],
        tool_call("read_file", path="app.py"),
        tool_call(
            "add_finding",
            file="app.py",
            severity="HIGH",
            category="SECURITY",
            issue="Hardcoded SECRET_KEY.",
            evidence='SECRET_KEY = "hardcoded"',
            recommendation="Load secrets from the environment.",
        ),
        tool_call("write_report"),
        {"type": "final_answer", "answer": "Review complete."},
    ]


def run_agent(*, llm, sandbox, config: AgentConfig | None = None):
    trace_recorder = TraceRecorder()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        project_scope=sandbox["scope"],
        report_path=sandbox["report_path"],
        config=config or AgentConfig(max_steps=20),
    )

    result = agent.run_with_result("Review . only.")
    trace = json.loads(trace_recorder.trace_path.read_text(encoding="utf-8"))
    summary_path = Path("run_summaries") / f"{trace_recorder.trace_path.stem}_summary.json"

    return agent, result, trace, trace_recorder.trace_path, summary_path


def rejected_steps(trace: list[dict]) -> list[dict]:
    return [
        step
        for step in trace
        if step.get("rejection") is not None
    ]


def assert_token_absent(*, token: str, texts: list[str]) -> None:
    for text in texts:
        assert token not in text


def test_escape_attempts_are_rejected_and_agent_recovers(sandbox):
    escape_paths = [
        "../canary.txt",
        str(sandbox["canary"]),
    ]
    llm = RecordingScriptedLLM(
        escape_then_recover_script(escape_paths=escape_paths),
    )

    agent, result, trace, trace_path, summary_path = run_agent(
        llm=llm,
        sandbox=sandbox,
    )

    assert result.is_completed is True
    assert agent.state.rejected_tool_call_count == 2
    assert agent.state.report_written is True
    assert agent.state.inspected_files == ["app.py"]

    rejections = rejected_steps(trace)

    assert [step["rejection"]["requested_path"] for step in rejections] == escape_paths

    for step in rejections:
        assert step["rejection"]["code"] == PATH_REJECTION_OUTSIDE_PROJECT_ROOT
        assert step["rejection"]["tool"] == "read_file"
        assert step["tool_result"] is None
        assert PATH_REJECTION_OUTSIDE_PROJECT_ROOT in step["error"]

    assert_token_absent(
        token=sandbox["token"],
        texts=[
            trace_path.read_text(encoding="utf-8"),
            summary_path.read_text(encoding="utf-8"),
            json.dumps(agent.state.to_dict()),
            json.dumps(agent.state.findings),
            Path(sandbox["report_path"]).read_text(encoding="utf-8"),
            result.answer or "",
            *llm.seen_messages,
        ],
    )


def test_junction_escape_is_rejected_at_runtime(sandbox):
    if os.name != "nt":
        pytest.skip("Junctions are Windows-only")

    import _winapi

    try:
        _winapi.CreateJunction(
            str(sandbox["outside_dir"]),
            str(sandbox["project"] / "escape"),
        )
    except OSError:
        pytest.skip("Creating junctions is not permitted here")

    llm = RecordingScriptedLLM(
        escape_then_recover_script(escape_paths=["escape\\leak.py"]),
    )

    agent, result, trace, trace_path, _summary_path = run_agent(
        llm=llm,
        sandbox=sandbox,
    )

    assert result.is_completed is True
    assert agent.state.discovered_files == ["app.py"]
    assert len(rejected_steps(trace)) == 1

    assert_token_absent(
        token=sandbox["token"],
        texts=[
            trace_path.read_text(encoding="utf-8"),
            *llm.seen_messages,
        ],
    )


def test_search_outside_root_is_rejected_at_runtime(sandbox):
    llm = RecordingScriptedLLM([
        tool_call("search_in_files", query=sandbox["token"][:10], path=".."),
        {"type": "final_answer", "answer": "done"},
    ])

    _agent, _result, trace, _trace_path, _summary_path = run_agent(
        llm=llm,
        sandbox=sandbox,
    )

    first = trace[0]

    assert first["rejection"]["tool"] == "search_in_files"
    assert first["rejection"]["code"] == PATH_REJECTION_OUTSIDE_PROJECT_ROOT


def test_repeated_escape_attempts_hit_rejected_tool_call_limit(sandbox):
    agent, result, trace, trace_path, _summary_path = run_agent(
        llm=AlwaysEscapeLLM(),
        sandbox=sandbox,
        config=AgentConfig(
            max_steps=20,
            max_rejected_tool_calls=3,
        ),
    )

    assert result.is_completed is False
    assert result.stop_reason_code == STOP_CODE_REJECTED_TOOL_CALLS
    assert agent.state.rejected_tool_call_count == 3
    assert len(trace) == 3

    for step in trace:
        assert step["rejection"]["code"] == PATH_REJECTION_OUTSIDE_PROJECT_ROOT

    assert sandbox["token"] not in trace_path.read_text(encoding="utf-8")


def test_agent_without_project_scope_rejects_file_tools(sandbox):
    trace_recorder = TraceRecorder()

    agent = Agent(
        llm=ScriptedBadLLM([
            tool_call("read_file", path="app.py"),
        ]),
        trace_recorder=trace_recorder,
        config=AgentConfig(max_steps=1),
    )

    agent.run_with_result("Review.")
    trace = json.loads(trace_recorder.trace_path.read_text(encoding="utf-8"))

    assert trace[0]["rejection"]["code"] == PATH_REJECTION_PROJECT_ROOT_NOT_CONFIGURED
    assert agent.state.rejected_tool_call_count == 1
