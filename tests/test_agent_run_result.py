import pytest

from agent_run_result import AgentRunResult
from agent_stop_reasons import STOP_MAX_STEPS


def test_completed_result_contains_answer():
    result = AgentRunResult.completed(
        "Review complete. Report written to report.md."
    )

    assert result.status == "completed"
    assert result.answer == "Review complete. Report written to report.md."
    assert result.stop_reason is None
    assert result.is_completed is True
    assert result.is_stopped is False


def test_stopped_result_contains_stop_reason():
    result = AgentRunResult.stopped(STOP_MAX_STEPS)

    assert result.status == "stopped"
    assert result.answer is None
    assert result.stop_reason == STOP_MAX_STEPS
    assert result.is_completed is False
    assert result.is_stopped is True


def test_completed_result_requires_non_empty_answer():
    with pytest.raises(ValueError):
        AgentRunResult.completed("")


def test_completed_result_rejects_stop_reason():
    with pytest.raises(ValueError):
        AgentRunResult(
            status="completed",
            answer="Done.",
            stop_reason=STOP_MAX_STEPS,
        )


def test_stopped_result_requires_non_empty_stop_reason():
    with pytest.raises(ValueError):
        AgentRunResult.stopped("")


def test_stopped_result_rejects_answer():
    with pytest.raises(ValueError):
        AgentRunResult(
            status="stopped",
            answer="Done.",
            stop_reason=STOP_MAX_STEPS,
        )


def test_invalid_status_is_rejected():
    with pytest.raises(ValueError):
        AgentRunResult(
            status="failed",
            answer="Done.",
        )

        