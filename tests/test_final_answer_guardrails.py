from agent import Agent
from agent_state import AgentState
from trace import TraceRecorder


class DummyLLM:
    def complete(self, messages, state=None):
        raise RuntimeError("DummyLLM should not be called in this test.")


def test_final_answer_allows_equivalent_windows_and_posix_paths():
    agent = Agent(
        llm=DummyLLM(),
        trace_recorder=TraceRecorder(),
        max_steps=1,
    )

    state = AgentState()
    state.report_written = True
    state.report_path = "report.md"
    state.discovered_files = [
        "sample_project/auth.py",
    ]
    state.inspected_files = [
        "sample_project\\auth.py",
    ]
    state.skipped_files = []

    allowed, reason = agent.validate_final_answer_allowed(
        state=state,
        answer="Review complete. Report written to report.md.",
    )

    assert allowed is True
    assert reason == ""