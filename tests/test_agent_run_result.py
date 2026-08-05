import pytest

from agent_run_result import AgentRunResult
from agent_stop_reasons import (
    STOP_CODE_INVALID_LLM_OUTPUTS,
    STOP_CODE_MAX_STEPS,
    STOP_INVALID_LLM_OUTPUTS,
    STOP_MAX_STEPS,
)

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
    result = AgentRunResult.stopped(STOP_MAX_STEPS, STOP_CODE_MAX_STEPS)

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
        AgentRunResult.stopped("", STOP_CODE_MAX_STEPS)


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

def test_from_dict_rejects_unknown_fields():
    with pytest.raises(ValueError):
        AgentRunResult.from_dict({
            "status": "completed",
            "answer": "Done.",
            "stop_reason": None,
            "unexpected": "value",
        })


def test_from_dict_rejects_missing_status_field():
    with pytest.raises(ValueError):
        AgentRunResult.from_dict({
            "answer": "Done.",
            "stop_reason": None,
            "stop_reason_code": None,
        })

def test_from_dict_rejects_missing_answer_field():
    with pytest.raises(ValueError):
        AgentRunResult.from_dict({
            "status": "completed",
            "stop_reason": None,
        })


def test_from_dict_rejects_missing_stop_reason_field():
    with pytest.raises(ValueError):
        AgentRunResult.from_dict({
            "status": "completed",
            "answer": "Done.",
        })        

def test_stopped_result_can_be_serialized_to_dict():
    result = AgentRunResult.stopped(STOP_MAX_STEPS, STOP_CODE_MAX_STEPS)

    assert result.to_dict() == {
        "status": "stopped",
        "answer": None,
        "stop_reason": STOP_MAX_STEPS,
        "stop_reason_code": STOP_CODE_MAX_STEPS,
    }   


def test_completed_result_can_be_serialized_to_dict():
    result = AgentRunResult.completed("Done.")

    assert result.to_dict() == {
        "status": "completed",
        "answer": "Done.",
        "stop_reason": None,
        "stop_reason_code": None,
    }


def test_completed_result_can_be_restored_from_dict():
    result = AgentRunResult.from_dict({
        "status": "completed",
        "answer": "Done.",
        "stop_reason": None,
        "stop_reason_code": None,
    })

    assert result == AgentRunResult.completed("Done.")


def test_stopped_result_can_be_restored_from_dict():
    result = AgentRunResult.from_dict({
        "status": "stopped",
        "answer": None,
        "stop_reason": STOP_MAX_STEPS,
        "stop_reason_code": STOP_CODE_MAX_STEPS,
    })

    assert result == AgentRunResult.stopped(STOP_MAX_STEPS, STOP_CODE_MAX_STEPS)

def test_stopped_result_rejects_unknown_stop_reason_code():
    with pytest.raises(ValueError):
        AgentRunResult.stopped(
            STOP_MAX_STEPS,
            "unknown_stop_code",
        )


def test_stopped_result_rejects_mismatched_stop_reason_and_code():
    with pytest.raises(ValueError):
        AgentRunResult.stopped(
            STOP_MAX_STEPS,
            STOP_CODE_INVALID_LLM_OUTPUTS,
        )


def test_from_dict_rejects_mismatched_stop_reason_and_code():
    with pytest.raises(ValueError):
        AgentRunResult.from_dict({
            "status": "stopped",
            "answer": None,
            "stop_reason": STOP_MAX_STEPS,
            "stop_reason_code": STOP_CODE_INVALID_LLM_OUTPUTS,
        })


def test_stopped_with_code_creates_stopped_result():
    result = AgentRunResult.stopped_with_code(STOP_CODE_MAX_STEPS)

    assert result.status == "stopped"
    assert result.answer is None
    assert result.stop_reason == STOP_MAX_STEPS
    assert result.stop_reason_code == STOP_CODE_MAX_STEPS
    assert result.is_stopped is True


def test_stopped_with_code_rejects_unknown_code():
    with pytest.raises(ValueError):
        AgentRunResult.stopped_with_code("unknown_stop_code")

                