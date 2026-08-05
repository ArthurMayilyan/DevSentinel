from agent_stop_reasons import (
    STOP_MAX_STEPS,
    STOP_REJECTED_FINAL_ANSWERS,
    STOP_REJECTED_TOOL_CALLS,
    STOP_INVALID_LLM_OUTPUTS,
)


def test_stop_reason_constants_are_non_empty_strings():
    stop_reasons = [
        STOP_MAX_STEPS,
        STOP_REJECTED_FINAL_ANSWERS,
        STOP_REJECTED_TOOL_CALLS,
        STOP_INVALID_LLM_OUTPUTS,
    ]

    for stop_reason in stop_reasons:
        assert isinstance(stop_reason, str)
        assert stop_reason.strip()


def test_stop_reason_constants_are_unique():
    stop_reasons = {
        STOP_MAX_STEPS,
        STOP_REJECTED_FINAL_ANSWERS,
        STOP_REJECTED_TOOL_CALLS,
        STOP_INVALID_LLM_OUTPUTS,
    }

    assert len(stop_reasons) == 4