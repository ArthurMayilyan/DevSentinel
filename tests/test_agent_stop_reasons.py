from agent_stop_reasons import (
    STOP_CODE_MAX_STEPS,
    STOP_CODE_REJECTED_FINAL_ANSWERS,
    STOP_CODE_REJECTED_TOOL_CALLS,
    STOP_CODE_INVALID_LLM_OUTPUTS,
    STOP_MAX_STEPS,
    STOP_REJECTED_FINAL_ANSWERS,
    STOP_REJECTED_TOOL_CALLS,
    STOP_INVALID_LLM_OUTPUTS,
    STOP_REASON_BY_CODE,
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

def test_stop_reason_codes_are_non_empty_unique_strings():
    stop_reason_codes = [
        STOP_CODE_MAX_STEPS,
        STOP_CODE_REJECTED_FINAL_ANSWERS,
        STOP_CODE_REJECTED_TOOL_CALLS,
        STOP_CODE_INVALID_LLM_OUTPUTS,
    ]

    for stop_reason_code in stop_reason_codes:
        assert isinstance(stop_reason_code, str)
        assert stop_reason_code.strip()

    assert len(set(stop_reason_codes)) == 4


def test_stop_reason_by_code_contains_all_stop_reasons():
    assert STOP_REASON_BY_CODE == {
        STOP_CODE_MAX_STEPS: STOP_MAX_STEPS,
        STOP_CODE_REJECTED_FINAL_ANSWERS: STOP_REJECTED_FINAL_ANSWERS,
        STOP_CODE_REJECTED_TOOL_CALLS: STOP_REJECTED_TOOL_CALLS,
        STOP_CODE_INVALID_LLM_OUTPUTS: STOP_INVALID_LLM_OUTPUTS,
    }    