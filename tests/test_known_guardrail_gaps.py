"""Known guardrail gaps, recorded as strict xfail tests.

When a gap is fixed the test starts passing, strict xfail turns that into a
failure, and the marker should be removed.
"""

import pytest

from devsentinel.core.agent import Agent
from devsentinel.core.agent_config import AgentConfig
from devsentinel.core.tool_path_utils import build_project_scope
from devsentinel.core.trace import TraceRecorder
from devsentinel.llm.bad_llm import ScriptedBadLLM


def tool_call(tool: str, **arguments) -> dict:
    return {
        "type": "tool_call",
        "tool": tool,
        "arguments": arguments,
    }


@pytest.mark.xfail(
    strict=True,
    reason=(
        "write_report/final_answer completeness is checked against the files "
        "the model discovered, and each list_files call replaces that list. "
        "Listing a narrower directory lets the agent finish without reading "
        "every project file."
    ),
)
def test_narrower_list_files_must_not_allow_early_report(tmp_path):
    (tmp_path / "a.py").write_text("X = 1\n", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.py").write_text("SECRET_KEY = 'x'\n", encoding="utf-8")

    agent = Agent(
        llm=ScriptedBadLLM([
            tool_call("list_files", path="."),
            tool_call("list_files", path="sub"),
            tool_call("read_file", path="sub/b.py"),
            tool_call(
                "add_finding",
                file="sub/b.py",
                severity="HIGH",
                category="SECURITY",
                issue="Hardcoded secret.",
                evidence="SECRET_KEY = 'x'",
                recommendation="Use configuration.",
            ),
            tool_call("write_report"),
            {"type": "final_answer", "answer": "done"},
        ]),
        trace_recorder=TraceRecorder(),
        project_scope=build_project_scope(root=tmp_path),
        report_path=str(tmp_path / "report.md"),
        config=AgentConfig(max_steps=10),
    )

    result = agent.run_with_result("Review . only.")

    assert not (result.is_completed and "a.py" not in agent.state.inspected_files)
