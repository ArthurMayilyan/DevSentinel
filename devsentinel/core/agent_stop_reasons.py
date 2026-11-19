STOP_CODE_MAX_STEPS = "max_steps"
STOP_CODE_REJECTED_FINAL_ANSWERS = "rejected_final_answers"
STOP_CODE_REJECTED_TOOL_CALLS = "rejected_tool_calls"
STOP_CODE_INVALID_LLM_OUTPUTS = "invalid_llm_outputs"


STOP_MAX_STEPS = "Agent stopped because max_steps limit was reached."

STOP_REJECTED_FINAL_ANSWERS = (
    "Agent stopped because rejected final answers limit was reached."
)

STOP_REJECTED_TOOL_CALLS = (
    "Agent stopped because rejected tool calls limit was reached."
)

STOP_INVALID_LLM_OUTPUTS = (
    "Agent stopped because invalid LLM outputs limit was reached."
)


STOP_REASON_BY_CODE = {
    STOP_CODE_MAX_STEPS: STOP_MAX_STEPS,
    STOP_CODE_REJECTED_FINAL_ANSWERS: STOP_REJECTED_FINAL_ANSWERS,
    STOP_CODE_REJECTED_TOOL_CALLS: STOP_REJECTED_TOOL_CALLS,
    STOP_CODE_INVALID_LLM_OUTPUTS: STOP_INVALID_LLM_OUTPUTS,
}